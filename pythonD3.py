'''Project 2 -CSE 6339
Group 5:
Yoga Vignesh Surathi
Ravitej Urikiti
Pratik Naik
Dilip Kumar Atchyuta

The following code is written in python and uses the flask module to display in web
This code calculates the association rules,cusum and the basic queries of task1
'''

import os
import csv
from flask import Flask, render_template,request, redirect, url_for, send_from_directory
from werkzeug import secure_filename
from decimal import Decimal
app = Flask(__name__)
import MySQLdb
import sys
from itertools import izip
from collections import Counter
import collections
import itertools 
from itertools import groupby
import pandas
import matplotlib.pyplot as plt
import numpy

#connecting to db for task 1 queries
db=MySQLdb.connect(host="127.0.0.1",port=3306,user="root",passwd="amarabindhu",db="mydb")
original_schema=MySQLdb.connect(host="127.0.0.1",port=3306,user="root",passwd="amarabindhu",db="project1")

# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'uploads/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = set(['csv','arff','txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
# For a given file, return whether it's an allowed type or not
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']

#Initialize the search dropdownlists'''
def fillData():
    ddlAge=[]
    ddlGender=[]
    ddlADC=[]
    cur= db.cursor()
    cur.execute("select distinct age from admission order by age")
    for row in cur.fetchall():
        ddlAge.append(dict([('age',row[0]),
                                     ('val',row[0]),
                                    ]))
    cur.execute("select distinct sex from admission order by sex")
    for row in cur.fetchall():
        s='M';
        if row[0]==1:
            s='M'
        else:
            s='F'
        ddlGender.append(dict([('sex',s),
                                     ('val',row[0]),
                                    ]))
    cur.execute("select distinct admitting_diagnosis_code from admission order by admitting_diagnosis_code")
    for row in cur.fetchall():
        ddlADC.append(dict([('admitting_diagnosis_code',row[0]),
                                     ('val',row[0]),
                                    ]))
    cur.close()
    variables={'ddlAge':ddlAge,'ddlGender':ddlGender,'ddlADC':ddlADC}
    return variables

'''Poplulate columns in web page selection'''
def getColumns(isCSV,csv_file):
    columns=[]
    variables={}
    if isCSV and csv_file:
        r = csv.reader(open('uploads/'+csv_file))
        colunm_names=r.next()
        cntr=0
        for col_name in colunm_names:
            col_name=col_name.strip()
            columns.append(dict([('col',col_name.replace(' ','_')),('col_no',cntr)])) 
            cntr=cntr+1
    else:        
        columnlist = [];
        cnt=0
        cur_sor=original_schema.cursor()
        cur_sor.execute("SHOW columns FROM healthcare")
        for column in cur_sor.fetchall():
            columns.append(dict([('col',column[0]),('col_no',cnt)]))
            cnt=cnt+1
        cur_sor.close()
    variables={'columns':columns}
    return variables
    
'''To find the different combintations in dataset using association'''
def getCombinations(cols,supp,confi,file_ds):
    straight_set=[]
    res_lista=[]    
    res_listb=[]      
    for subset in itertools.combinations(cols, 2):
        straight_set.append(subset)    
    #reverse_set= [(b, a) for a, b in straight_set]  
    res_lista = [x[0] for x in straight_set]
    res_listb = [x[1] for x in straight_set]    
    col_names=[]
    r = csv.reader(open('uploads/'+file_ds))
    col_names=r.next()
    cntr=0
    str1=[]
    str2=[]
    finalstr=[]
    for item in res_lista:
        set10=col_names[res_lista[cntr]]
        set11=col_names[res_listb[cntr]]        
        str1=Association(res_lista[cntr],res_listb[cntr],set10,set11,confi,supp,file_ds)
        set20=col_names[res_listb[cntr]]
        set21=col_names[res_lista[cntr]]
        str2=Association(res_listb[cntr],res_lista[cntr],set20,set21,confi,supp,file_ds)
        cntr=cntr+1
        finalstr.append(str1+str2)
    return ''.join(finalstr)

'''To find the association rules'''
def Association(csv_col_ref1,csv_col_ref2,set_col1,set_col2,confi,supp,file_ds):

    col1=[]
    col2=[]
    combicol={}
    displayList=[] 
    csv_df = csv.reader(open('uploads/'+file_ds))
    next(csv_df)
    for row in csv_df:
            if row[csv_col_ref1]!=' ' and row[csv_col_ref2]!=' ':
                col1.append(row[csv_col_ref1])
                col2.append(row[csv_col_ref2])
    columnCntr=Counter(col1)
    df = pandas.DataFrame({'A': col1, 'B': col2}) 
    result = df.groupby(['A','B']).size()
    combicol=result.to_dict()
    cntr=0
    str_list=[]
    for combi in combicol:
        displayList.append(combi)
        support=float(combicol[combi])/1477
        likeCol=list(displayList[cntr])
        confidence=float(combicol[combi])/float(columnCntr[likeCol[0]])       
        if confidence>=confi and support>=supp:          
            str_list.append("Rule:  %s %s  ==>  %s %s , (%s) support:(%f) , confidence:(%f) &"
                            % (set_col1,combi[0],set_col2,combi[1],combicol[combi],support,confidence))     
            cntr=cntr+1
    return ''.join(str_list)

'''DIsplay top 10 queries'''
@app.route("/task1")
def task1():
    top10=[]
    queryNo=int(request.args.get('q'))
    cur= db.cursor()
    heading1=""
    if queryNo==1:
        query="top10deathratio"
        cur.callproc(query)
        heading1="Top 10 admission diagnoses with the highest 'death on discharge' ratio"
        col1="Death Ratio"
        col2="Admitting Diagnosis Code"
        for row in cur.fetchall():
            top10.append(dict([('feature',row[2]),('ADC',row[3])
                                    ]))
    if queryNo==2:
        query="top10expensive"
        heading1="Top 10 most expensive admission diagnoses"
        cur.callproc(query)
        col1="Expense or Total cost"
        col2="Admitting Diagnosis Code"
        for row in cur.fetchall():
            top10.append(dict([('feature',row[1]),('ADC',row[0])
                                    ]))
    if queryNo==3:
        query="top10lengthofstay"
        heading1="Top 10 diagnoses with the highest average length of stay"
        cur.callproc(query)
        col1="Avg length of stay"
        col2="Admitting Diagnosis Code"
        for row in cur.fetchall():
            top10.append(dict([('feature',row[1]),('ADC',row[0])
                                    ]))
    cur.close()
    values={'top10':top10,'heading1':heading1,'col1':col1,'col2':col2}
    return render_template('details.html',**values)


@app.route("/")
def index():
    return render_template('index.html')
  
           
@app.route("/search")
def search():
    variables=fillData()
    return render_template('basic.html',**variables)

'''display the results in the web for the given search query'''
@app.route("/searchresult",methods=['GET','POST'])    
def post():
    age=int(request.form["ageValue"])
    sex=int(request.form["sexValue"])
    if sex ==1:
        s='M'
    else:
        s='F'
    ADC_raw=request.form["adcValue"]
    ADC=ADC_raw.strip()
    cur= db.cursor()
    result11=[]
    result12=[]
    result21=[]
    result22=[]
    result31=[]
    result32=[]
    absolute_differenceA2=deviation_ratioD2=deviation_ratioA2=absolute_differenceD2=absolute_difference1=None
    absolute_difference3=deviation_ratio1=deviation_ratio3=None
    length1=length2=statusA1=statusD1=statusA2=statusD2=cost2=cost1=0.000
    if age and sex and ADC:
        heading1="For diagnosis code %s" % ADC
        query="select age,sex,admitting_diagnosis_code,AVG(length_of_stay)"
        query=query+" from admission,discharge_details where a_id=admission_a_id and age=%d and sex=%d and admitting_diagnosis_code like '%s%%'"
        query=query+" group by age,sex,admitting_diagnosis_code"
        query=query % (age,sex,ADC)
        cur.execute(query);
        for row in cur.fetchall():
            length1=float(row[3])
            result11.append(dict([('age',row[0]),('sex',s),('admitting_diagnosis_code',row[2]),('length_of_stay',row[3])
                                   ]))
        heading2="For all diagnosis codes"
        query="select age,sex,admitting_diagnosis_code,AVG(length_of_stay)"
        query=query+" from admission,discharge_details where a_id=admission_a_id and age=%d and sex=%d "
        query=query+"group by age,sex"
        query= query % (age,sex)
        cur.execute(query)
        for row in cur.fetchall():
            length2=float(row[3])
            result12.append(dict([('age',row[0]),('sex',s),('admitting_diagnosis_code',row[2]),('length_of_stay',row[3])
                                   ]))
        
        if length1 and length2:
            deviation_ratio1= (length1/length2)*100
            absolute_difference1=abs(length2-length1)
        
        query="select Count(*) /(select count(*) from admission)*100 AliveRatio, (1-(count(*)/(select count(*) from admission)))*100 DeathRatio "
        query+="from admission,discharge_details where a_id=admission_a_id and age = %d and sex = %d and admitting_diagnosis_code like '%s%%' "
        query+="and discharge_status = 'A' group by age,sex,admitting_diagnosis_code;"
        query=query % (age,sex,ADC)
        cur.execute(query);
        for row in cur.fetchall():
            if row[0] or row[1]:
                statusA1=float(row[0])
                statusD1=float(row[1])
                result21.append(dict([('age',age),('sex',s),('admitting_diagnosis_code',ADC),('alive_ratio',row[0]),('death_ratio',row[1])
                                       ]))
        
        
        query="select Count(*) /(select count(*) from admission)*100 AliveRatio, (1-(count(*)/(select count(*) from admission)))*100 DeathRatio "
        query+="from admission,discharge_details where a_id=admission_a_id and age = %d and sex = %d and discharge_status = 'A' "
        query+="group by age,sex;"
        query=query % (age,sex)
        cur.execute(query);
        for row in cur.fetchall():
            if row[0] or row[1]:
                statusA2=float(row[0])
                statusD2=float(row[1])
                result22.append(dict([('age',age),('sex',s),('admitting_diagnosis_code',ADC),('alive_ratio',row[0]),('death_ratio',row[1])
                                       ]))
        if statusA1 and statusA2:
            deviation_ratioA2= (statusA1/statusA2)*100
            absolute_differenceA2=abs(statusA2-statusA1)
        if statusD1 and statusD2:
            deviation_ratioD2= (statusD1/statusD2)*100
            absolute_differenceD2=abs(statusD2-statusD1)
        
        query="select age,sex,admitting_diagnosis_code,AVG(total_price)"
        query=query+" from admission,billing where a_id=admission_a_id and age=%d and sex=%d and admitting_diagnosis_code like '%s%%' "
        query=query+"group by age,sex,admitting_diagnosis_code"
        query=query  % (age,sex,ADC)
        cur.execute(query);
        for row in cur.fetchall():
            cost1=float(row[3])
            result31.append(dict([('age',row[0]),('sex',s),('admitting_diagnosis_code',row[2]),('total_cost',row[3])
                                   ]))
        query="select age,sex,admitting_diagnosis_code,AVG(total_price)"
        query=query+" from admission,billing where a_id=admission_a_id and age=%d and sex=%d"
        query=query+" group by age,sex"
        query=query  % (age,sex)
        cur.execute(query);
        for row in cur.fetchall():
            cost2=float(row[3])
            result32.append(dict([('age',row[0]),('sex',s),('admitting_diagnosis_code',row[2]),('total_cost',row[3])
                                   ]))
        if cost1 and cost2:
            deviation_ratio3= (cost1/cost2)*100
            absolute_difference3=abs(cost2-cost1)
    variables=fillData()
    variables.update({'result11':result11,
               'result12':result12,'result21':result21,'result22':result22,'result31':result31,'result32':result32,
               'heading1':heading1,'heading2':heading2,'ageVal':age,'sexVal':sex,'adcVal':ADC_raw
               })
    variables.update({'absolute_difference1':absolute_difference1,
                      'absolute_differenceA2':absolute_differenceA2,
                      'absolute_differenceD2':absolute_differenceD2,
                      'absolute_difference3':absolute_difference3,
                      'deviation_ratio1':deviation_ratio1,'deviation_ratioA2':deviation_ratioA2,
                      'deviation_ratioD2':deviation_ratioD2,
                      'deviation_ratio3':deviation_ratio3})
    
    return render_template('basic.html',**variables)
     


@app.route("/classify")
def classify():
    return render_template('classify.html')


'''Display rules'''
@app.route("/rules/<filename>",methods=('GET','POST'))
def rules(filename):
    variables={}
    if(filename):
        variables=getColumns(1,filename)
        column_index= request.form.getlist('attr')
        indexes=[]
        for col_index in column_index:
            indexes.append(int(col_index))
        support = float(request.form['support'])
        confidence = float(request.form['confidence'])
        ruleslist=getCombinations(indexes,support,confidence,filename).split('&')        
        variables.update({'ruleslist':ruleslist,'support':support,'confidence':confidence})
    else:
        variables=getColumns(0,None)
    variables.update({'filename':filename})
    return render_template('association.html',**variables)


@app.route("/association")
def association():
    return render_template('association.html')

'''Function to upload the csv file and read it'''
@app.route('/upload', methods=['POST'])
def upload():
    variables={}
    # Get the name of the uploaded file
    file_csv = request.files['file']
    # Check if the file is one of the allowed types/extensions
    if file_csv and allowed_file(file_csv.filename):
        # Make the filename safe, remove unsupported chars
        filename = secure_filename(file_csv.filename)
        # Move the file form the temporal folder to
        # the upload folder we setup
        file_csv.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        variables=getColumns(1,filename)
        variables.update({'filename':filename})
        # Redirect the user to the uploaded_file route, which
        # will basicaly show on the browser the uploaded file
    return render_template('association.html',**variables)



@app.route("/about")
def about():
    return render_template('about.html')

'''Find the cusum of the given values'''
@app.route("/cusumcal",methods=('GET','POST'))
def display():
    input_set=request.form["cvalues"]
    cvals = input_set.split(",")
    tempdataset=[int(x) for x in cvals]
    Ref_mean =float(request.form["mean"])
    Ref_SD = float(request.form["sd"])
    Ref_Sigma =float(request.form["sigma"])
    #totsum = sum(tempdataset);            #Sum of array values
    #mean = totsum/len(tempdataset);      #Average value
    leng = len(tempdataset);
    temp =0;
    arr = [];
    while True:
        arr.append(tempdataset[temp]-Ref_mean);
        temp = temp +1;
        if temp == leng:
            break
    cusum_array = [];
    cusum_temp =0;
    temp1 = 0;

    while True: #Generation of cusum array
        cusum_temp = cusum_temp+arr[temp1];
        if temp1==0:    
            cusum_array.append(0 + arr[0]);
            temp1 = temp1 +1;                                   
        else :          
            cusum_array.append(cusum_temp);
            temp1 = temp1 +1;                     
        if temp1 == leng:
            break

    threshold = Ref_SD*Ref_Sigma;
    #Threshold calculation
    val=1
    s_no=[]
    while val<=leng:
        s_no.append(val)
        val=val+1
    val=1   
    sets=[]
    for s in cusum_array:
        sets.append(dict([('s_no',val),('cumsum_val',s)]))
        val=val+1
    filename="uploads/cumsum_output.csv"
    with open(filename, "wb") as f:
        writer = csv.writer(f)
        writer.writerow(["serial","cusum"])
        rows = zip(s_no,cusum_array)
        for row in rows:
            writer.writerow(row)
    finalset=[]
    for n in sets:
        if n['cumsum_val']>=threshold:
            print n['cumsum_val']
            finalset.append(dict([('s_no',n['s_no']),('cumsum_val',n['cumsum_val'])]))
    y_limit=0
    if max(cusum_array)>threshold:
         y_limit=max(cusum_array)+1
    else:
         y_limit=threshold+1
    plt.plot(s_no,cusum_array);
    plt.ylim([min(cusum_array),y_limit])
    plt.xlim([0,leng+1])
    plt.xlabel('S.No')
    plt.ylabel('Cusum')
    plt.title('Cusum Generation')
    plt.axhline(y=threshold,color='r')
    plt.savefig('static/output.png')
    plt.clf() 
    output={'finalset':finalset,'sets':sets,'threshold':threshold,'filename':filename,'cvals':cvals,'Ref_mean':Ref_mean,'Ref_Sigma':Ref_Sigma,'Ref_SD':Ref_SD}
    return render_template("cumsum.html",**output)


@app.route("/cumsum")
def cumsum():
    return render_template("cumsum.html")


@app.errorhandler(500)
def page_not_found(e):
    print e
    return render_template('404.html', error = e)
    
if __name__ == "__main__":
    app.run(debug=False)

                                    
