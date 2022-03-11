!/bin/bash
echo "Enter Instance Name: "
read instance

echo "Rebuilding $instance"

rm -rf console-output

mkdir console-output/
stream="./console-output/$instance-stream.log"
ostack="./console-output/$instance-ostack.log"
touch $stream $ostack

openstack server rebuild $instance --image debian10_lxde --wait
echo "Instance rebuild in progress..."

echo "--------------------------------------"
echo "Starting Console Log Stream at $(date)"
echo "--------------------------------------"
start=$(date +%s.%N)
while true
do
    openstack console log show $instance > $ostack
    cat $ostack | diff $stream - | sed '1 d' | sed 's/^> //g'
    diff $stream $ostack | sed '1 d' | sed 's/^< //g' >> $stream
    if grep -q "Session 1 of user" $stream
    then
        break
    fi
    sleep 3
done
end=$(date -u +%s.%N)
runtime=$( echo "$end - $start" | bc -l )

echo ""
echo "---------------------------------------"
echo "Instance build took $runtime seconds"
echo "---------------------------------------"