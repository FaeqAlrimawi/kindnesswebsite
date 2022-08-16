from ..models import Aok, NonAok, NLPModel, ModelAok, ModelNonAok, db
import pandas as pd 
import xlsxwriter
from ..control import load_Model_and_Features


def populateModelTable():
    # global model
    # global features_file
    
    # if not model:
    model, features_file = load_Model_and_Features()
    
   
    if len(NLPModel.query.all()) ==0 : 
        # print("###  creating a new model")       
        new_model = NLPModel(model=str(model), features=features_file)
        
        if new_model:
            db.session.add(new_model)
            res = db.session.commit()  
        else:
            print("problem creating a new model")  
        
    # newAok = Aok(act="testing")
    # db.session.add(newAok)
    # db.session.commit()
    
    # models = NLPModel.query.all()
    
    # for model in models:
    #     newModelAok = ModelAok(model_id=model.id, aok_id=newAok.id)
    #     db.session.add(newModelAok)
    #     db.session.commit()
    #     print(str(model.model))   
         
         
def populateDatabaseWithAoKs():
    
    # already loaded
    if Aok.query.first() is not None:
        return
    
    # file_name = url_for('website/static', filename='actsOfKindness.xlsx')
    file_name = './website/static/actsOfKindness.xlsx'
    sheet_name = 'All_AoKs'
    description_column = 'Description'
    trained_col = 'trained'
    df = pd.read_excel(file_name, sheet_name=sheet_name, usecols=[description_column, trained_col])
    
    model = NLPModel.query.first()
    
    if model is None:
        return 
    
    newAoks = []
    newModelAoKs = []
    for element in df.values:
    
        if len(element) >0 :
            newAok = Aok(act=element[0])
            db.session.add(newAok)
            db.session.commit()
            # if newAok:
            #     newAoks.append(newAok)
                # print(newAok.act)

            isTrained = element[1]
            if isTrained == 'yes':        
                newModelAok = ModelAok(model_id=model.id, aok_id=newAok.id)
                newModelAoKs.append(newModelAok)
                    
                    
    # if len(newAoks) > 0:
    #     db.session.add_all(newAoks)
    #     db.session.commit()    
        
    if len(newModelAoKs) >0:
        db.session.add_all(newModelAoKs)
        db.session.commit()    
        
    return      
          

def populateDatabaseWithNonAoKs():
    
    # already loaded
    if NonAok.query.first() is not None:
        # print("already added non-aoks")
        return
    
    # file_name = url_for('website/static', filename='actsOfKindness.xlsx')
    file_name = './website/static/actsOfKindness.xlsx'
    sheet_name = 'All_NonAoks'
    description_column = 'Description'
    trained_col = 'trained'
    df = pd.read_excel(file_name, sheet_name=sheet_name, usecols=[description_column, trained_col])
    
    model = NLPModel.query.first()
    
    if model is None:
        return
    
    newNonAoks = []
    newModelNonAoKs = []
    for element in df.values:
    
        if len(element) >0 :
            newNonAok = NonAok(act=element[0])
            # if newNonAok:
            newNonAoks.append(newNonAok)
            db.session.add(newNonAok)
            db.session.commit()
            # print(newAok.act)

            isTrained = element[1]
            if isTrained == 'yes':        
                newModelNonAok = ModelNonAok(model_id=model.id, non_aok_id=newNonAok.id)
                newModelNonAoKs.append(newModelNonAok)
                    
                    
    # if len(newNonAoks) > 0:
    #     db.session.add_all(newNonAoks)
    #     db.session.commit()    
        
    if len(newModelNonAoKs) >0:
        db.session.add_all(newModelNonAoKs)
        db.session.commit()    
        
    return                
      
        
def exportDB():
      
    '''
    exports aoks to a cvs file
    
    '''   
    query = db.session.query(Aok).all()
    nonAokQuery = db.session.query(NonAok).all()
    excelFile = 'website/static/acts.xlsx'
    # with open(csvFile, 'w') as fp:
    #     postgres_copy.copy_from(query, fp, db.engine, format='csv', header=True)
    #     print("control.exportDB(): copy completed")
        
    # print(query)    
    # fp = open(csvFile, 'w', encoding="utf-8") 
    # strAoks = []
    # for aok in query:
    #     strAok = "%s,%s"%(aok.act, aok.source)
    #     strAoks.append(strAok)
        
    # fp.writelines(strAoks)
    # fp.close
    
    workbook = xlsxwriter.Workbook(excelFile)
    worksheet = workbook.add_worksheet("aoks")
    worksheetNonAoK = workbook.add_worksheet("nonaoks")
    
    # Start from the first cell.
    # Rows and columns are zero indexed.
    row = 1
    
    # headers
    worksheet.write(0, 0, "Act")
    worksheet.write(0, 1, "Source")
    worksheet.write(0, 2, "Date Added")
    worksheet.write(0, 3, "Trained")
    
    count  =0
    # iterating through content list
    for aok in query :
        
        # write operation perform
        worksheet.write(row,0, aok.act)
        
        worksheet.write(row, 1, aok.source)
        
        worksheet.write(row, 2, aok.date)
        
        isTrained = aok.isTrained()
        worksheet.write(row, 3, "yes" if isTrained else "no")
       
        if isTrained:
           count +=1
    
        # incrementing the value of row by one
        # with each iterations.
        row += 1
        
    print("########### ", count)
    row = 1
     # headers
    worksheetNonAoK.write(0, 0, "Act")
    
    # iterating through content list
    for nonAok in nonAokQuery :
        
        # write operation perform
        worksheetNonAoK.write(row,0, nonAok.act)
    
        # incrementing the value of row by one
        # with each iterations.
        row += 1
         
    # worksheetNonAoK.close() 
    
    workbook.close()    