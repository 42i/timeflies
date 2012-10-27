
make timeflies.pdf

tifl=../src/timeflies.py
version=`$tifl --version`
date=`date +%Y-%m-%d`
dir=TimeFlies-$version-$date
zipfile=../../$dir.zip

mkdir $dir

cp timeflies.pdf change-log.txt $dir

# timeflies.py -> timeflies
cp $tifl $dir/timeflies

zip -r $zipfile $dir

rm -rf $dir

unzip -l $zipfile

