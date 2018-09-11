
# coding: utf-8

# In[ ]:


import urllib
import xml.etree.cElementTree as etree
import pandas as pd
import re
import sys

class FeedParser:
    MAX_WORD_COUNT = 7
    def __init__(self, fname):
        self.fname = fname        
        self.isUrl = False
        if fname.startswith("http"):
            self.isUrl = True
        self.url_offer_df = self.read()
    def clean(self, string):
        c_string = string.replace(u'\u2069'," ")
        c_string = c_string.replace(u'\u2010',"-")
        return(c_string)
    
    def read(self):
        available = []
        category = []
        vendor = []
        vendorCode = []
        typePrefix = []
        model = []
        url = []
        name = []
        price = []
        #entire feed
        filePath = self.fname
        if self.isUrl:
            filePath = urllib.request.urlopen(self.fname)
            
        tree = etree.ElementTree(file=filePath)
        root = tree.getroot()
        
        categories = {}
        for cat in root.iter("category"):
            categories[cat.attrib["id"]] = self.clean(cat.text)
        counter = 0    
        for offer in root.iter("offer"):
            available.append(offer.attrib["available"]=="true")
            try:
                    category.append(self.clean(categories[offer.find("categoryId").text]))
            except Exception:
                    category.append(None)
                
            try:
                    vendor.append(self.clean(offer.find("vendor").text))
            except AttributeError:
                    vendor.append(None)
                    
            try:
                    vendorCode.append(self.clean(offer.find("vendorCode").text))
            except AttributeError:
                    vendorCode.append(None)
                    
            try:
                    url.append(self.clean(offer.find("url").text))
            except AttributeError:
                    url.append(None)
                    
            try:
                    typePrefix.append(self.clean(offer.find("typePrefix").text))
            except AttributeError:
                    typePrefix.append(None)
                    
            try:
                    model.append(self.clean(offer.find("model").text)) 
            except AttributeError:
                    model.append(None)
                    
            try:
                    name.append(self.clean(offer.find("name").text)) 
            except AttributeError:
                    name.append(None)
            try:
                    price.append(self.clean(offer.find("price").text)) 
            except AttributeError:
                    price.append(None)

                    
        url = [re.sub(r"[?&]?utm_.*$", "", x) for x in url]     
        
        return(pd.DataFrame({"available" : available,
                             "category" : category, 
                             "vendor" : vendor, 
                             "vendorCode" : vendorCode, 
                             "typePrefix" : typePrefix, 
                             "model" : model, 
                             "name" : name,
                             "url" : url,
                             "price": price}))

        
    def create_advertisements(self, templates, header_template = None, name_template = None, progressThread = None):
        nsteps = len(templates)
        
        result = pd.DataFrame(columns=['keyword', 'header', 'url', 'name'])
        
        if len(templates) == 0:
            rerturn(result)
            
        if  header_template == None: 
            header_template = templates[0]
            
        if  name_template == None: 
            name_template = templates[0]
        
        
       
        
        niter = 0
    
        for template in templates:
            niter += 1
            print("template num %d from %d" % (niter, len(templates)))
            if (progressThread != None):
                progressThread.countChanged.emit(int(niter * 100/nsteps))
                
            #get sebset of columns
            tmpl = list(set(template + header_template + name_template + ["url"]))
            
            df = self.url_offer_df.loc[self.url_offer_df.available, tmpl]
            df = df.reset_index(drop=True)
            #remove None lines
            df = df.dropna()
            
            if (len(template) == 1):
                keyword = df.loc[:,template[0]]
            else:
                keyword = df[template].astype(str).apply(lambda x: " ".join(x),1)
            
            for i in keyword.index:
                keyword[i] = re.sub(r"[();.,!?()\+\-\[\]«»\"']", "", keyword[i])
                keyword[i] = re.sub(r"&nbsp", " ", keyword[i])
            
            if (len(header_template) == 1):
                header = df.loc[:,header_template[0]].astype(str).apply(lambda x: "#" + x + "#",1)
            else:
                header = df[header_template].astype(str).apply(lambda x: "#" + " ".join(x) + "#",1)
            
            for i in header.index:
                header[i] = re.sub(r"[();.,!?()\+\-\[\]«»\"']", "", header[i])
                header[i] = re.sub(r"&nbsp", " ", header[i])
            
            name = df[name_template].astype(str).apply(lambda x: " ".join(x), 1)
            if (len(name_template) == 1):
                name = df.loc[:,name_template[0]]
            else:
                name = df[name_template].astype(str).apply(lambda x: " ".join(x), 1)
            
            for i in name.index:
                name[i] = re.sub(r"[();.,!?()\+\-\[\]«»\"']", "", name[i])
                name[i] = re.sub(r"&nbsp", " ", name[i])
            
            url = df.url    
            
            result = result.append(pd.DataFrame({"keyword":keyword,             
                                    "header": header, "url":url, "name":name}), ignore_index=True)
        
        
        not_nums_only = result.keyword.apply(lambda x: re.match("^\d+$",x) == None)
        result = result[not_nums_only]
        
        
        url_df = pd.DataFrame({"url":result.url.unique()})
        url_df["num"] = url_df.index + 1
        
        

        result = result.merge(url_df, on = "url")
        
        result = result.sort_values("num")
        result = result[["name", "num", "keyword", "url"]]
        
        result["wordCount"] = result.keyword.apply(lambda x: len(x.split()))
        
        return(result)
    
    def get_tag_statistic(self):        
        return(dict(round(self.url_offer_df[["category", "vendor", "vendorCode", "typePrefix", "model", "name", "url"]].count()/self.url_offer_df.shape[0]*100).astype(int)))
    
    def get_offer_count(self):
        return(self.url_offer_df.shape[0])
    
    def get_offer_top(self, count = 5):
        df = self.url_offer_df.loc[self.url_offer_df.available, :]
        return(df[["category", "vendor", "vendorCode", "typePrefix", "model", "name", "url"]].iloc[0:count, :])
    
    def get_offer_top_with_stat(self, count = 5):
        stat = self.get_tag_statistic()
        top = self.get_offer_top(count)
        result = top.append(pd.DataFrame({"category" : [str(stat["category"])+"%"], 
                                          "vendor" : [str(stat["vendor"])+"%"], 
                                          "vendorCode" : [str(stat["vendorCode"])+"%"], 
                                          "typePrefix" : [str(stat["typePrefix"])+"%"], 
                                          "model" : [str(stat["model"])+"%"], 
                                          "name" : [str(stat["name"])+"%"],
                                          "url" : [str(stat["url"])+"%"]}), ignore_index=True)
        return(result)
        

