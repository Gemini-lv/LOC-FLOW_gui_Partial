"""
#####################step 2####################
print("################\nseparate P and S picks\n###############")
# seperate the picks in picks.csv into p and s picks
pickfile = './results/picks.csv'
output1 = 'temp.p'
output2 = 'temp.s'
prob_threshold = 0.5
samplingrate = 0.01 #samplingrate of your data, default 100 hz

f = open(output1,'w')
g = open(output2,'w')
data = pd.read_csv(pickfile, parse_dates=["begin_time", "phase_time"])
data = data[data["phase_score"] >= prob_threshold].reset_index(drop=True)

data[["year", "mon", "day"]] = data["begin_time"].apply(lambda x: pd.Series([f"{x.year:04d}", f"{x.month:02d}", f"{x.day:02d}"]))
data["ss"] = data["begin_time"].apply(lambda x: (x - datetime.fromisoformat(f"{x.year:04d}-{x.month:02d}-{x.day:02d}")).total_seconds())
data[["net", "name", "loc", "channel"]] = data["station_id"].apply(lambda x: pd.Series(x.split(".")))
data["dum"] = pd.Series(np.ones(len(data)))
data["phase_amp"] = data["phase_amp"] * 2080 * 20 
# why 2080? see https://docs.obspy.org/_modules/obspy/signal/invsim.html
# 2080*20 is because PhaseNet didn’t convolve the response into the Wood-Anderson type and a factor of 20 is experimentally adopted to correct the amplitude.
# Please consider re-calculating the magnitude using the other script 'calc_mag.py'
data["phase_time"] = data["ss"] + data["phase_index"] * samplingrate
data[data["phase_type"] == "P"].to_csv(output1, columns=["year", "mon", "day", "net", "name", "dum", "phase_time", "phase_score", "phase_amp"], index=False, header=False)
data[data["phase_type"] == "S"].to_csv(output2, columns=["year", "mon", "day", "net", "name", "dum", "phase_time", "phase_score", "phase_amp"], index=False, header=False)

for i in range(len(data["file_name"])):
    (pickfile,junk) = data["file_name"][i].split('/')
    if os.path.isdir(pickfile):
        shutil.rmtree(pickfile)
#####################step 3####################
print("################\ncreat pick files by date and station name\n###############")
# separate picks based on date and station names
# the picks maybe not in order, it is fine and REAL
# will sort it by their arrival
command = "pick2real -Ptemp.p -Stemp.s &"
print(command)
os.system(command)
#os.remove(output1) 
#os.remove(output2) 
"""
import os
import shutil
import pandas as pd
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QAction, QMenuBar, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal
# phasenet检测页面，这个页面还是简单的
def load_config():
    with open("config.ini", "r") as f:
        lines = f.readlines()
    # 构造一个字典来存储配置项
    config = {}
    for line in lines:
        if "=" in line:
            key, value = line.split("=")
            config[key.strip()] = value.strip()
    return config

# 该类实现以上功能的多线程处理，避免主线程卡顿
class post_process(QThread):
    signal_progress = pyqtSignal(str)
    signal_finish = pyqtSignal(int) 
    signal_error = pyqtSignal(str) 
    def __init__(self, result_path,prob_threshold,samplingrate, parent=None):
        super().__init__(parent)
        self.result_path = result_path
        self.prob_threshold = prob_threshold
        self.pickfile = self.result_path + '/picks.csv'
        self.output1 = self.result_path + '/temp.p'
        self.output2 = self.result_path + '/temp.s'
        self.samplingrate = samplingrate
        self.config = load_config()

    
    def run(self):
        try:
            self.signal_progress.emit("separating P and S picks...")
            print("################\nseparate P and S picks\n###############")
            if not os.path.exists(self.pickfile)
                self.signal_error.emit("picks.csv not found")
                return
            data = pd.read_csv(self.pickfile, parse_dates=["begin_time", "phase_time"])
            data = data[data["phase_score"] >= self.prob_threshold].reset_index(drop=True)
            data[["year", "mon", "day"]] = data["begin_time"].apply(lambda x: pd.Series([f"{x.year:04d}", f"{x.month:02d}", f"{x.day:02d}"]))
            data["ss"] = data["begin_time"].apply(lambda x: (x - datetime.fromisoformat(f"{x.year:04d}-{x.month:02d}-{x.day:02d}")).total_seconds())
            data[["net", "name", "loc", "channel"]] = data["station_id"].apply(lambda x: pd.Series(x.split(".")))
            data["dum"] = pd.Series(np.ones(len(data)))
            data["phase_amp"] = data["phase_amp"] * 2080 * 20
            data["phase_time"] = data["ss"] + data["phase_index"] * self.samplingrate
            data[data["phase_type"] == "P"].to_csv(self.output1, columns=["year", "mon", "day", "net", "name", "dum", "phase_time", "phase_score", "phase_amp"], index=False, header=False)
            data[data["phase_type"] == "S"].to_csv(self.output2, columns=["year", "mon", "day", "net", "name", "dum", "phase_time", "phase_score", "phase_amp"], index=False, header=False)
            # done
            pick2real_path = self.config['loc_flow_path'] + 'src\REAL\bin\pick2real'
            #command = "pick2real -P" + self.output1 + " -S" + self.output2 + " &"
            command = pick2real_path + " -P" + self.output1 + " -S" + self.output2 + " &"
            os.system(command)
            self.signal_finish.emit(1)
            return
        except Exception as e:
            self.signal_error.emit(str(e))
            return
        
"""
import math
import obspy.taup
import numpy as ny
import sys
from obspy.taup import TauPyModel
from obspy.taup.taup_create import build_taup_model
build_taup_model("mymodel.nd") 
# when you prepare the model, please consider interpolating 
# the velocity model above the majority of seismicity (e.g., a few km/layer)
# so that VELEST (mode=0) can update it
# TauP, velest, and hypoinverse don't like low velocity layers...
model = TauPyModel(model="mymodel")

dist=1.4 #dist range in deg.
dep=20 #depth in km

ddist=0.01 #dist interval, be exactly divided by dist
ddep=1 #depth interval, be exactly divided by dep

ndep=int(dep/ddep)+1
ndist=int(dist/ddist)+1

with open("ttdb.txt", "w") as f:
    #f.write("dist dep tp ts tp_slowness ts_slowness tp_hslowness ts_hslowness p_elvecorr s_elvecorr\n")
    for idep in range(0,ndep,1): # in depth
        for idist in range(1,ndist,1): # in horizontal
            dist = idist*ddist
            dep = idep*ddep
            print(dep,dist)
            arrivals = model.get_travel_times(source_depth_in_km=dep, distance_in_degree=dist, phase_list=["P","p","S","s"])
            #print(arrivals)
            i = 0
            pi = 0
            si = 0
            while(i<len(arrivals)):
                arr = arrivals[i]
                i = i + 1
                if((arr.name == 'P' or arr.name == 'p') and pi == 0):
                    pname = arr.name
                    p_time = arr.time
                    p_ray_param = arr.ray_param*2*ny.pi/360
                    p_hslowness = -1*(p_ray_param/111.19)/math.tan(arr.takeoff_angle*math.pi/180)
                    pi = 1

                if((arr.name == 'S' or arr.name == 's') and si == 0):
                    sname = arr.name
                    s_time = arr.time
                    s_ray_param = arr.ray_param*2*ny.pi/360
                    s_hslowness = -1*(s_ray_param/111.19)/math.tan(arr.takeoff_angle*math.pi/180)
                    si = 1
                if(pi == 1 and si == 1):
                    break

            if(pi == 0 or si == 0):
                sys.exit("Error, no P or S traveltime, most likely low velocity issue: dist=%.2f, dep=%.2f, tp=%.2f, ts=%.2f" % (dist,dep,p_time,s_time))
                    
            f.write("{} {} {} {} {} {} {} {} {} {}\n".format(dist, dep, p_time,s_time, p_ray_param, s_ray_param, p_hslowness, s_hslowness, pname, sname))

"""
class taup_tt(QThread):
    signal_progress = pyqtSignal(str)
    signal_finish = pyqtSignal(int)
    signal_error = pyqtSignal(str)
    def __init__(self, model_path, ttdb_path, dist,dep,ddist,ddep,model, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self.ttdb_path = ttdb_path
        self.model = model
        self.dist = dist
        self.dep = dep
        self.ddist = ddist
        self.ddep = ddep
        
    
    def run(self):
        try:
            import math
            import obspy.taup
            import numpy as ny
            import sys
            from obspy.taup import TauPyModel
            from obspy.taup.taup_create import build_taup_model
            self.signal_progress.emit("building ttdb...")
            build_taup_model(self.model_path) 
            # when you prepare the model, please consider interpolating 
            # the velocity model above the majority of seismicity (e.g., a few km/layer)
            # so that VELEST (mode=0) can update it
            # TauP, velest, and hypoinverse don't like low velocity layers...
            model = TauPyModel(model=self.model_path)
            ndep = int(self.dep/self.ddep)+1
            ndist = int(self.dist/self.ddist)+1
            with open(self.ttdb_path, "w") as f:
                for idep in range(0,ndep,1): # in depth
                    self.signal_progress.emit(f"building ttdb...{idep}/{ndep}")
                    for idist in range(1,ndist,1): # in horizontal
                        dist = idist*self.ddist
                        dep = idep*self.ddep
                        print(dep,dist)
                        arrivals = model.get_travel_times(source_depth_in_km=dep, distance_in_degree=dist, phase_list=["P","p","S","s"])
                        i = 0
                        pi = 0
                        si = 0
                        while(i<len(arrivals)):
                            arr = arrivals[i]
                            i = i + 1
                            if((arr.name == 'P' or arr.name == 'p') and pi == 0):
                                pname = arr.name
                                p_time = arr.time
                                p_ray_param = arr.ray_param*2*ny.pi/360
                                p_hslowness = -1*(p_ray_param/111.19)/math.tan(arr.takeoff_angle*math.pi/180)
                                pi = 1

                            if((arr.name == 'S' or arr.name == 's') and si == 0):
                                sname = arr.name
                                s_time = arr.time
                                s_ray_param = arr.ray_param*2*ny.pi/360
                                s_hslowness = -1*(s_ray_param/111.19)/math.tan(arr.takeoff_angle*math.pi/180)
                                si = 1
                            if(pi == 1 and si == 1):
                                break

                        if(pi == 0 or si == 0):
                            sys.exit("Error, no P or S traveltime, most likely low velocity issue: dist=%.2f, dep=%.2f, tp=%.2f, ts=%.2f" % (dist,dep,p_time,s_time))

                        f.write("{} {} {} {} {} {} {} {} {} {}\n".format(dist, dep, p_time,s_time, p_ray_param, s_ray_param, p_hslowness, s_hslowness, pname, sname))
            self.signal_progress.emit("building ttdb finished")
            self.signal_finish.emit(1)
        except Exception as e:
            self.signal_error.emit(str(e))


runREAL = """

$year0 = "2016";
$month0 = "10";
$day0 = "14";
$nday = "1";

$ID=0;
$phaseSAall = "phaseSA_allday.txt";
open(OUT,">$phaseSAall");

for($i=0; $i<$nday; $i++){
	if($i == 0){
	$year = $year0; $month=$month0; $day = $day0;
	}else{
	($year,$month,$day) = &Timeadd($year0,$month0,$day0,1);}
	$year0 = $year; $month0 = $month; $day0 = $day;
	print"$year $month $day\n";
	if(length($month)==1){$month = "0".$month;} 
	if(length($day)==1){$day = "0".$day;} 
	$outfile ="$year$month$day";

    # -D(nyear/nmon/nday/lat_center)
    $D = "$year/$month/$day/42.75";
    # -R(rx/rh/tdx/tdh/tint[/gap/GCarc0/latref0/lonref0]])
    #$R = "0.1/20/0.02/2/5"; # small gride size
    $R = "0.1/20/0.04/2/5"; # large grid size
    # -G(trx/trh/tdx/tdh)
    $G = "1.4/20/0.01/1";
    # -V(vp0/vs0/[s_vp0/s_vs0/ielev])
    $V = "6.2/3.4";
    # -S(np0/ns0/nps0/npsboth0/std0/dtps/nrt/[drt/nxd/rsel/ires])
    #$S = "3/2/8/2/0.5/0.1/1.8/0.35"; # for small grid size
    $S = "3/2/8/2/0.5/0.1/1.2/0.0"; # for large grid size
    
    # thresholds may change with pickers, here for rough testing
    if ($picker==0){
        $dir = "../Pick/STALTA/$year$month$day"; # use STA/LTA picks
    }elsif($picker==1){
        $dir = "../Pick/PhaseNet/$year$month$day"; # use PhaseNet picks
    }elsif($picker==2){
  	$dir = "../Pick/OBST-EQT/picks/$year$month$day"; # use EQT or OBST picks
    }else{
        printf STDERR "please choose 0: STALTA or 1: PhaseNet or 2: EQT/OBST";
    }
    $station = "../Data/station.dat";
    $ttime = "./tt_db/ttdb.txt";

    system("REAL -D$D -R$R -S$S -G$G -V$V $station $dir $ttime");
    print"REAL -D$D -R$R -S$S -G$G -V$V $station $dir $ttime\n";
    `mv catalog_sel.txt $outfile.catalog_sel.txt`;
    `mv phase_sel.txt $outfile.phase_sel.txt`;
    `mv hypolocSA.dat $outfile.hypolocSA.dat`;
    `mv hypophase.dat $outfile.hypophase.dat`;

    $hypophase_file = $outfile.".hypophase.dat";
    open(EV,"<$hypophase_file");
    @par = <EV>;
    close(EV);

    foreach $_(@par){
	    chomp($_);
            $beigin = substr($_,0,1);
            if($beigin eq "#"){
            ($jk,$year,$month,$day,$hour,$min,$sec,$evla,$evlo,$evdp,$evmg,$EH,$EZ,$RMS,$nn) = split(" ",$_);chomp($nn);
            $nn=$nn+$ID;
            printf OUT "%1s %04d %02d %02d %02d %02d %06.3f  %8.4f  %9.4f  %6.3f %5.2f %7.2f %7.2f %7.2f      %06d\n",$jk,$year,$month,$day,$hour,$min,$sec,$evla,$evlo,$evdp,$evmg,$EH,$EZ,$RMS,$nn;
            }else{print OUT "$_\n";}	
    }
    $ID=$nn;
}
close(OUT);

#events with large number of picks and small station gap
#can be used for velocity model updation in VELEST
$numps = 30; # minimum number of P and S picks
$gap = 180; # largest station gap

$phaseall = phaseall_flag;
$catalogall = catalogall_flag;
$catalogSAall = catalogSAall_flag;
$phasebest = phasebest_flag;

`cat *.phase_sel.txt > $phaseall`;
`cat *.catalog_sel.txt > $catalogall`;
`cat *.hypolocSA.dat > $catalogSAall`;

&PhaseBest($phaseall,$phasebest,$numps,$gap); # maybe used for velocity model updating in VELEST
&PhaseAll($phaseall); # will be used in VELEST 

sub PhaseAll{
    my($file) = @_;
	open(JK,"<$file");  
	@par = <JK>;
	close(JK);
    
    $num = 0;
    open(OT,">$file");
	foreach $file(@par){
        chomp($file);
		($test,$jk) = split(' ',$file);
		if($test =~ /^\d+$/){
			($jk,$year,$mon,$dd,$time,$ot,$std,$lat,$lon,$dep,$mag,$jk,$nofp,$nofs,$nofps,$nboth,$gap) = split(' ',,$file);
			($hour,$min,$sec) = split('\:',$time);
			$num++;
			print OT "# $year  $mon  $dd   $hour    $min    $sec    $lat    $lon    $dep     $mag     0.0     0.0    0.0    $num\n";
		}else{
			($net,$station,$phase,$traveltime,$pick,$amplitude,$res,$prob,$baz) = split(' ',$file);
			print OT "$station $pick $prob $phase\n";
		}
	}
    close(OT);
}

sub PhaseBest{
    my($filein,$fileout,$numps,$gap0) = @_;
	open(JK,"<$filein");  
	@par = <JK>;
	close(JK);
    
    $num = 0;
    open(OT,">$fileout");
	foreach $file(@par){
		($test,$jk) = split(' ',$file);
        if($test =~ /^\d+$/){
            ($jk,$year,$mon,$dd,$time,$ot,$std,$lat,$lon,$dep,$mag,$jk,$nofp,$nofs,$nofps,$nboth,$gap) = split(' ',,$file);
            ($hour,$min,$sec) = split('\:',$time);
            $iok = 0;
            if($nofps >= $numps && $gap <= $gap0){
			    $num++;
			    print OT "# $year  $mon  $dd   $hour    $min    $sec    $lat    $lon    $dep     $mag     0.0     0.0    0.0   $num\n";
                $iok = 1;
            }
         }else{
             if($iok == 1){
            ($net,$station,$phase,$traveltime,$pick,$amplitude,$res,$prob,$baz) = split(' ',$file);
            print OT "$station $pick $prob $phase\n";
            }
		}
	}
    close(OT);
}


sub Timeadd{
   my($yyear,$mm,$dday,$adday) = @_;
   $dday = $dday + $adday;	
   if (($mm==1) || ($mm==3) || ($mm==5) || ($mm==7) || ($mm==8) || ($mm==10) || ($mm==12)){
      if ($dday >31) {
         $dday = 1;
         $mm = $mm + 1;
         if ($mm > 12) {
            $mm = 1;
            $yyear = $yyear + 1;
         }
      }
   }    
   if (($mm==4) || ($mm==6) || ($mm==9) || ($mm==11)){
      if ($dday >30) {
         $dday = 1;
         $mm = $mm + 1;
         if ($mm > 12) {
            $mm = 1;
            $yyear = $yyear + 1;
         }
      }
   }    
   if ($mm == 2) {
      if ((($yyear%4 == 0) && ($yyear%100 != 0)) || ($yyear%400 == 0)){
         if ($dday >29) {
            $dday = 1;
            $mm = $mm + 1;
         }
      }
      else{
        if ($dday >28) {
            $dday = 1;
            $mm = $mm + 1;
         }
      }
   }

   my @time = ($yyear,$mm,$dday);
   return(@time);
}

"""
class REAL(QThread):
    signal_progress = pyqtSignal(str)
    signal_finish = pyqtSignal(int)
    signal_error = pyqtSignal(str)
    def __init__(self, result_path, build+

class REAL_GUI(QMainWindow):

            
                
            

