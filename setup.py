# bootstrap pybuiler upload
import sh
sh.pyb('package')
sh.pyb('upload')
