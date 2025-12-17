#1762785769
ll
#1762785775
chmod +x run.sh 
#1762785777
ll
#1762785821
eval "$(/sw/qubientai/miniconda3/bin/conda shell.bash hook)”
;
#1762785857
eval "$(/sw/qubientai/miniconda3/bin/conda shell.bash hook)”
;
#1762785866
eval "$(/sw/qubientai/miniconda3/bin/conda shell.bash hook)”
#1762785887
eval "$(/sw/qubientai/miniconda3/bin/conda shell.bash hook)"
#1762785900
conda activate summary_env
#1762785903
./run.sh
#1762785951
echo 'export PATH=$HOME/local/nodejs/bin:$PATH' >> ~/.bashrc
#1762785952
source ~/.bashrc
#1762785962
conda activate summary_env
#1762785978
cat .bashrc 
#1762786080
./run.sh
#1762794014
ll
#1762794119
cd local/
#1762794119
ll
#1762794125
cd ..
#1762794126
ll
#1762797972
du -h
#1762797996
du -hsx * | sort -rh | head -n 10
#1762798096
dhdd
#1762798107
df -h
#1762785499
ll
#1762785507
chmod +x ./run.sh 
#1762785509
./run.sh
#1762785608
./stop.sh 
#1762785747
ll
#1762785754
su -
#1762785375
ll
#1762785406
conda activate summary_env
#1762785430
pwd
#1762785447
eval "$(/sw/qubientai/miniconda3/bin/conda shell.bash hook)"
#1762785468
conda activate summary_env
#1762785475
./run.sh
#1762785484
su -
#1762817234
du -h --max-depth=1
#1762817247
ll
#1762817260
du -ah --max-depth=1
#1762817299
du -h --max-depth=2 | sort -hr | head -20
#1762817310
du -h
#1762817314
df -h
#1762817323
cd ..
#1762817326
ll
#1762817328
cd root
#1762817328
ll
#1762817331
su -
ll
stt_start
stt_status
cd /~
cd /
ll
pwd
stt_status
su - 
stt_stop
stt_start
stt_status
stt_stop
ll
exit
ll
wget https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-5.6.3.tgz
java --version
ll
cd local/
ll
cd jdk-17/
ll
# curl로 다운로드
curl -O https://archive.apache.org/dist/jmeter/binaries/apache-jmeter-5.6.3.tgz
# 압축 해제
tar -xzf apache-jmeter-5.6.3.tgz
# 실행 권한 부여
chmod +x apache-jmeter-5.6.3/bin/jmeter
chmod +x apache-jmeter-5.6.3/bin/jmeter.sh
cd ..
cd jdk-17/
ll
mv apache-jmeter-5.6.3 ../
mv apache-jmeter-5.6.3.tgz  ../
ll
cd ..
ll
mv apache-jmeter-5.6.3 ../
mv apache-jmeter-5.6.3.tgz ../
ll
cd ..
ll
vi .bashrc
source .bashrc
java --version
vi .bashrc
ll
pwd
cd local/
ll
cd ..
vi .bashrc
source .bashrc
java --version
cd apache-jmeter-5.6.3/
./bin/jmeter -n -t test_plan_gateway.jmx -Jthreads=1 -Jloops=30 -Jrampup=0 -l results_1thread_30loops.jtl
./bin/jmeter -n -t test_plan_gateway.jmx -Jthreads=30 -Jloops=1 -Jrampup=0 -l results_30concurrent.jtl -e -o report_30concurrent/
cd ..
ll
./stop.sh 
./run.sh 
cd apache-jmeter-5.6.3/
./bin/jmeter -n -t test_plan_gateway.jmx -Jthreads=30 -Jloops=1 -Jrampup=0 -l results_30concurrent.jtl -e -o report_30concurrent/
cd ..
./stop.sh 
ll
tar -xvf llm-api.tar 
ll
mkdir etc
mv llm-api-0.0.1-SNAPSHOT.jar etc/
cd llm-ap
cd llm-api
ll
cd build/
ll
cd libs/
ll
mv llm-api-0.0.1-SNAPSHOT.jar ../../../
cd ..
ll
./run.sh
cd llm-api/
./gradlew build
chmod +x gradlew
./gradlew build
./gradlew clean bootJar -x test
ll
mv build
cd build/
cd libs/
ll
mv llm-api-0.0.1-SNAPSHOT.jar ../../../
cd ..
ll
./stop.sh 
./run.sh 
./stop.sh 
cd llm-api/
./gradlew clean bootJar -x test
cd build/libs/
ll
mv llm-api-0.0.1-SNAPSHOT.jar ../../../
cd ..
cd llm-api/
ll
cd ..
./stop.sh 
./run.sh
./stop.sh 
./run.sh 
cd llm-api/
./gradlew clean bootJar -x test
cd build/libs/
mv llm-api-0.0.1-SNAPSHOT.jar ../../../
cd ..
ll
./stop.sh 
./run.sh 
cd apache-jmeter-5.6.3/
./bin/jmeter -n -t test_plan_gateway.jmx -Jthreads=30 -Jloops=1 -Jrampup=0 -l results_30concurrent.jtl -e -o report_30concurrent/
cd ..
./stop.sh 
./run.sh
cd apache-jmeter-5.6.3/
./bin/jmeter -n -t test_plan_gateway.jmx -Jthreads=30 -Jloops=1 -Jrampup=0 -l results_30concurrent.jtl -e -o report_30concurrent/
cd ..
ll
cd ..
ll
cd sw/qubientai/
ll
su ~
su - qubientai 
exit
