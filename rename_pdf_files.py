# -*- coding: utf-8 -*-
"""
Created on Wed Mar 13 15:58:08 2019
@author: Victor Pinto

Stuff to do 

 - Some old PDF don't have DOI and it is not possible to read the text from the 
   pages (error)
 - some titles have stuff in {} that I don't want, but others do have words I
   want to keep. Still need to remove the {}
 - Change the two list structure of journals to a dict with name:abbreviation
   
Suff I'm too lazy to do

 - Delete a PDF if its duplicate (script will end in error right now)
 
  
"""

import PyPDF2
import os
import string
import requests
import bibtexparser
import re 
from habanero import Crossref

# Set the directory where the PDF files are located
pdfDir = r'C:\Users\Victor\OneDrive\Research\library'
doi_re = re.compile("10.(\d)+/([^\s\>\"\<])+")
cnt = 0

#Test a single case, then do a for.
for filename in os.listdir(pdfDir):
    file = os.path.join(pdfDir, filename)
    
    # Open each file, read metadata and first page (for DOI) 
    # using PyPDF2 (then close the file)
    f = open(file, 'rb')
    
    pdfFile = PyPDF2.PdfFileReader(f, strict=False)
    info = pdfFile.getDocumentInfo()
    
    # can get info1.title (for example)
    if '/WPS-ARTICLEDOI' in info:
        doi = info['/WPS-ARTICLEDOI']
    else:
        try:
            print("No DOI in PDF Metadata. Trying PDF text for: "+ filename)
            text = pdfFile.getPage(0).extractText()
            doi = doi_re.search(text).group(0)
            doi = doi.rstrip('.')
        except:
            print('No DOI for: '+filename)
            f.close()
            continue

#            try:
#                print("NO DOI in PDF text. Trying Crossref for: "+filename)
#                cr = Crossref()
#                find = cr.works(query = info.title, limit=5)
#                doi = find['message']['items'][0]['DOI']
#            except:
#                print('No DOI for: '+filename)
#                f.close()
#                continue

    f.close()
    
    # Request data from DOI.org in bibtex format
    # Other options for formats 
    # "application/x-bibtex"
    # "text/html"
    # "text/bibliography"
    url = "http://dx.doi.org/" + doi
    headers = {"accept": "application/x-bibtex"}
    r = requests.get(url, headers = headers)

    # Parse bibtex into a dict
    bibData = bibtexparser.loads(r.text)
    bib = bibData.entries
    
    # Get the author list
    try:
        authors = bib[0]["author"].split('and')
        authorLastname = authors[0].split()
        
        if len(authors) == 1:
            author = authorLastname[-1]
            
        if len(authors) == 2:
            auth2 = authors[1].split()
            author = authorLastname[-1]+'_and_'+auth2[-1]
        
        if len(authors) > 2:
            author = authorLastname[-1]+'_et_al'
    except:
        print("No authors identified for PDF")
        continue
    
    # Work with the journals
    journals = [u"Geophysical Research Letters", 
                u"Journal of Geophysical Research: Space Physics",
                u"Journal of Geophysical Research",
                u"Space Science Reviews",
                u"Advances in Space Research",
                u"Earth, Planets and Space",
                u"Physical Review Letters",
                u"Science",
                u"Nature",
                u"Annales Geophysicae",
                u"Journal of Atmospheric and Solar-Terrestrial Physics"
                ]
    
    jabv = ["GRL", "JGR", "JGR", "SSR", "ASR", "EPS", "PRL", "Sci", "Nat",
            "AG", "JASTP"]
    
    try:
        if bib[0]["journal"] in journals:
            journal = jabv[journals.index(bib[0]["journal"])]
        else:
            print("Journal not defined: "+bib[0]["journal"])
            continue
    except:
        print("No journal defined for PDF")
        continue
    
    title = bib[0]["title"].split(" ")
    title = "_".join(title)
    title = re.sub("[\{\[].*?[\)\}]", "", title)
    
    toJoin = [author,bib[0]["year"],journal,title]    
    pdftitle = "-".join(toJoin)
    
    valid = "-_.() %s%s" % (string.ascii_letters, string.digits)
    pdftitle = ''.join(c for c in pdftitle if c in valid)+".pdf" 
    
    full_new = os.path.join(pdfDir, pdftitle)
    os.rename(file, full_new)  

    if cnt == 25:
        break
    else:
        cnt += 1
        