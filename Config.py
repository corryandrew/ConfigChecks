import re
import teradata
import getpass
import smtplib
import datetime
import sys
import base64
import csv
import os, errno, os.path, shutil
import configparser
import datetime


os.system('cls')
print("\n" *4)
print("                                                                   CSV Checker ")
print("                                                                   ============")
print("                                                Tests USR_PROD_COMB and USR_OFFG_COMB CSV files only ")
print("                                                ----------------------------------------------------")
#print("\n" *1)
print("                                                1. Checks EOF blank line. ")
print("                                                2. Checks matching number of columns per file type. ")
print("                                                3. Checks for space and comma issues. ")
print("                                                4. Checks for date format issues. ")
print("\n" *1)

def check_date(DateTime, Num):    
  error="N"
  format_date="%Y-%m-%d %H:%M:%S"
  try:
      if DateTime != datetime.datetime.strptime(DateTime, format_date).strftime(format_date):
        raise ValueError
  except ValueError:
       error="Y"

  if error == "Y":
      try:
          format_date="%Y/%m/%d %H:%M:%S"
          if DateTime == datetime.datetime.strptime(DateTime, format_date).strftime(format_date):
              error="N"
          else:
              raise ValueError
      except ValueError:
          error="Y"

  if error=="Y":
      print(" Date issue, field " + str(Num) + " on line " + str(line_number) + " DateTime = " + DateTime)
  return error

config = configparser.ConfigParser()
config.read("C:\Python3_7\My Scripts\Config Solution\db.cnfg")
Sys = config.get('DB connection info','Sys')
User = config.get('DB connection info','User')
PassWd = config.get('DB connection info','PassWd')
 
os.chdir("C:\Python3_7\My Scripts\Config Solution")
thisdir = os.getcwd()

Final_Dir2=("C:\Python3_7\My Scripts\Config Solution\Final_Files")
if not os.path.exists(Final_Dir2):
  os.makedirs(Final_Dir2)
##Jeff added creation of last line dir
  os.makedirs(thisdir + "\Last_Line\\")

#NB NB, user must open the "cmd" as administrator (right click on "Run as administrator")
for r, d, f in os.walk(Final_Dir2):
    for file in f:
        if ".csv" in file:
            os.remove(os.path.join(r, file))
    break

PassWd2='\"'+ PassWd + '\"'

udaExec = teradata.UdaExec (appName="Config Report", version="1.0",
        logConsole=False)
session = udaExec.connect(method="ODBC", Authentication="LDAP", system=Sys, username=User, password=PassWd2);

report_name = "Config Report"
num=0
Dest=(thisdir + "\Last_Line\\")
ProbFiles="\n"
HaveCSV="N"
TotalCSV=0
file_list=[]
print("")

allfiles = os.listdir(thisdir)
for all_f in allfiles:
    if ".csv" in all_f:
      TotalCSV = TotalCSV + 1

print("Testing "+ str(TotalCSV)+ " CSV file(s)")
#print("=================================")
print("" *5)

#print("Starting Tests...")
#print("" *5)

#Checks
files = os.listdir(thisdir)
files.sort()
for f in files:
    if ".csv" in f:
      HaveCSV="Y"
      read_file=open(f)
      for line in read_file:
        Last_Line=(line)

      if not "\n" in Last_Line:
        print("EOF blank line test. Files moved to \\Last_Line folder")
        print("----------------------------------------------------")
        print("No backslash n detected in the last line of file: " + "\n" + f)
        print("")
        read_file.close()
        #ProbFiles=(ProbFiles + "  Moved " + f + " to Last_Line directory \n")
        ProbFiles=(ProbFiles + f +"\n")
        shutil.move(thisdir+"\\"+f , Dest+f)



if HaveCSV == 'N':
  print("No CSV files to be processed")
  print("============================")
  sys.exit(2)
   
# r=root, d=directories, f = files
for r, d, f in os.walk(thisdir):
    for file in f:
        if ".csv" in file:
            currt_dir=os.getcwd()
            file_error="N"
            Fname=file .split('.')[0]
            JName=Fname .split('_OT')[0]
            JNum="_OT" + Fname .split('_OT')[1]
            
            sqlquery = ['''
	     	 select count(*)
                 from dbc.columns
		 where databasename='PRD_STG_USR'
                 and tablename = ''' "'" + JName + "'"
	        ]
          
            for row in session.execute(sqlquery):
             Table_column_count = (row[0])
             Table_column_count = Table_column_count -3
    #added "-3" because there appears to be 3 extra columns for USR tables on Prod
            Len=len(file)
            read_file=open(file)
            read_file2=csv.reader(read_file, delimiter=",")

            print("")
            print("Checking file " + file)
            print("-------------" + "-" *Len)
            
            line_number=1
            for line in read_file2:
                #SPACE_COMMA='N'
                
                col_number=len(line)
                if Table_column_count != col_number:
                     print(" Delimiter count does not match table column count " + file + ", line " + str(line_number))
                     print("            Table has " + str(Table_column_count) + ", line " + str(line_number) + " has " + str(col_number))
                     file_error="Y"

                CSV=str(line)
                
                #RES=re.search(r" \' \?\',", CSV)
                re_sp_comma=re.search(r"(,\' | \',)", CSV)
                if re_sp_comma:
                    print(" Space and comma issue, line " + str(line_number))
                    #SPACE_COMMA='Y'
                    file_error="Y"
                
                #RES=re.search(r", \' \?\'", CSV)
#                re_comma_sp=re.search(", ", CSV)
                #if RES and SPACE_COMMA == 'N':
#                if re_comma_sp:
#                    print(" Comma and space issue, line " + str(line_number))
#                    file_error="Y"

                Rec=str(line).split(', ')

                if "usr_prod_comb_" in file:
                    
                    DateTime=Rec[5].strip('\'')
                    Num=6
                    error_res=check_date(DateTime, Num)
                    if error_res == "Y":
                        file_error="Y"
                      
                    DateTime=Rec[8].strip('\'')
                    Num=9
                    if DateTime != '?':
                        error_res=check_date(DateTime, Num)
                        if error_res == "Y":
                            file_error="Y"

                elif  "usr_offg_comb_" in file:
                    DateTime=Rec[4].strip('\'')
                    Num=5
                    error_res=check_date(DateTime, Num)
                    if error_res == "Y":
                        file_error="Y"

                    DateTime=Rec[5].strip('\'')
                    Num=6
                    error_res=check_date(DateTime, Num)
                    if error_res == "Y":
                        file_error="Y"

                    DateTime=Rec[6].strip('\'')
                    Num=7
                    error_res=check_date(DateTime, Num)
                    if error_res == "Y":
                        file_error="Y"

                    DateTime=Rec[8].strip('\'')
                    Num=9
                    error_res=check_date(DateTime, Num)
                    if error_res == "Y":
                        file_error="Y"
                        
                else:
                    print("Unknown file " + file)
                    file_error="Y"
                    
                line_number= line_number + 1
            
            #create an array to hold unique list of names (going to write all the files with a common name
            #to the array)
            if file_error == "N":    
              if (num) == 0:
                  file_list = [JName + ":" + JNum]
                  num = num +1
              else:
               file_list.insert(num,JName + ":" + JNum)
               num = num +1
            else:
                ProbFiles=(ProbFiles + JName + JNum + ".csv\n")
                
            read_file.close()
    break  

unique_list=set(file_list)

Dest=(thisdir + "\Final_Files\\")
Proc_Files="\n"


if len(file_list):
  for File_Name in file_list:
      New_File=File_Name .split(':')[0]
      #New_File_CSV = (Dest + New_File + ".csv")
      Old_File=New_File + File_Name .split(':')[1] + ".csv"

      sqlquery = ['''
	     	     locking row for access select source_object,source_object || '_' || (next_seq (format '9999')) || '.csv' as next_file_name_version from (select
                      source_object, max(file_name_seq)+1 as next_seq from prd_tec_ctl.tc_file
                      f,prd_tec_ctl.tc_file_type ft where f.file_type_id = ft.file_type_id and (f.file_type_id like 'usr%' or f.file_type_id like 'map%') and file_status in
                      ('Archived', 'Removed') group by 1) x
                      where SOURCE_OBJECT  = ''' "'" + New_File + "'"
	        ]

      for row in session.execute(sqlquery):
          New_File_CSV =(Dest + (row[1]))
                
      file_exists=os.path.isfile(New_File_CSV)
      Proc_Files=(Proc_Files + Old_File + "\n")
    
      if not file_exists:
        open(New_File_CSV, "a")

      with open(Old_File) as f:
          with open(New_File_CSV, "a") as new:
            for line in f:
                new.write(line)

print("\n" *4)
print("Files that were processed. It is now joined and sequenced in \\Final_Files folder:")
print("==================================================================================")
print(Proc_Files)

print("" *2)
print("Files that were NOT processed:")
print("=============================")
print(ProbFiles)


