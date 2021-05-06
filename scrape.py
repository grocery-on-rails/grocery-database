import requests, os
from bs4 import BeautifulSoup
import json
from collections import OrderedDict
import xmltodict


# Make a request

def progressBar(current, total, barLength = 100):
    percent = float(current) * 100 / total
    arrow   = '-' * int(percent/100 * barLength - 1) + '>'
    spaces  = ' ' * (barLength - len(arrow))

    print('Progress: [%s%s] %d %%  %d / %d' % (arrow, spaces, percent,current,total), end='\r')


cat=['Vegetables','Fruits','Seafood','Meat','Bakery','Dairy','Drinks','Pantry']

overlap={}
url_list=[]
product_list=[]
sub={}

#scraping all subcategories, and products' urls in each category
print ("Scraping Subcategories and products' urls")
for i,category in enumerate(cat):
	progressBar(i,len(cat))
	url_cat="https://www.kibsons.com/shopping/CategoryProducts?searchType=CATEGORY&searchText="+category+"&searchcategory="
	page_cat = requests.get(url_cat)
	soup = BeautifulSoup(page_cat.content, 'html.parser')
	da=soup.select('a[onclick*="'+category+'"] ')
	# me=BeautifulSoup(da).select("span")
	# data = [[cell.text for cell in row]
#                         for row in BeautifulSoup(da,'lxml')("span")]
	sub[category]=[]
	try:
		for i in range(1,100):
			if da[i].text.strip() not in sub[category]:
				sub[category].append(da[i].text.strip())
				
	except:
		try:
			sub[category].remove("VIEW ALL")
			sub[category].remove(category.upper())
		except:
			pass
	
	
	#scrape the urls for all products in all categories with overlap detection and assigning each item to all the categories it is under
	urls=soup.select('div.product > p.product-title > a.products-name')
	for url in urls:
		link='https://www.kibsons.com'+url.get('href')
		if link in url_list:
			if link in overlap.keys():
				overlap[link].append(category)
			else:
				overlap[link]=[category]
			continue

		
		url_list.append(link)
out=[]

#write the list of categories and their subcategories
for ca in cat:
	out.append({"category": ca, "subcategory":sub.get(ca)})
with open('subcategory.json', 'w') as the_file:
	the_file.write(json.dumps(out, indent=4))
print("\nNumber of urls:"+str(len(url_list)))

#further scraping the urls for all products in all subcategories with overlap detection and assigning each item to all the subcategories it is under
print ("Further scraping Products' url and assigning them to their subcategories")
for i,category in enumerate(sub.keys()):
	
	progressBar(i,len(sub.keys()))
	for item in sub[category]:
		typ="FAMILIES"
		if not item.isupper():
			typ= "custom"
		url_cat="https://www.kibsons.com/shopping/CategoryProducts?searchType="+typ+"&searchText="+item+"&searchcategory="+category
		#print(item)
		page_cat = requests.get(url_cat)

		soup = BeautifulSoup(page_cat.content, 'html.parser')

		urls=soup.select('div.product > p.product-title > a.products-name')
		#getting the url of each product
		for url in urls: 
			link='https://www.kibsons.com'+url.get('href')
			#if it exists then just add the subcategory to the attributes 
			if link in url_list:
				if link in overlap.keys():
					if item not in overlap[link]:
						overlap[link].append(item)
				else:
					overlap[link]=[item]
				continue
		url_list.append(link)
print("\nNumber of urls:"+str(len(url_list)))	
# print(json.dumps(overlap,indent=4))



#scraping every product's information
print ("Scraping Products")
for i, url in enumerate(url_list[:40]):
	
	progressBar(i,len(url_list))
	# Extract first <h1>(...)</h1> text
	page = requests.get(url)
	soup = BeautifulSoup(page.content, 'html.parser')
	subcategory=[]
	try:
		subcategory = soup.select('div.detail-text > p')[0].text.split(">")[1].strip().split(maxsplit=1)
	except:
		print(url)
		continue
	# if a product in mltiple subcategories, add all of them to its sbucategory attribute
	if overlap.get(url,False):
		subcategory.extend(overlap[url])
	#desc = soup.select('div#tab_01 > p')[0].text
	name = soup.select('div.box-details-info > div.product-name > h1')[0].text.strip()
	# image = soup.select('div.product-display-image:nth-child(1) > img.main-image-det')[0]
	# src = image.get('src')
	# alt = image.get('alt')
	#image_data.append({"src": src, "alt": alt})
	price = soup.select('h1.product-price > span')[0].text.strip()
	try:
		unit = soup.select('h1.product-price')[0].text.strip().split(' / ')[1].strip()
	except:
		pass

	country = soup.select('p.details-origin')[0].text.strip()
	quantity = soup.select('div.options > p')[0].text.strip()
	#scrape images
	image_list=[]
	try:
		for i in range(0,10):
			img = soup.select('div.product-display-image-slider-single:nth-child('+str(i+1)+') > img')[0].get('src')
			image_list.append(img)
	except:
		pass
	#scrape description
	desc = soup.select('div.tab')[0].text.strip().split("\n")
	info_list={}
	# if exists, scrape other infromation such as nutrition tables, storage infromation
	for i in range(0,5):
		try:
			desc[i]=desc[i].strip()
			info=soup.select('div#tab_0'+str(i+1)+'')[0]
			# NUTRITIONAL INFORMATION is an html table, so extract its values and make them into a list 
			if desc[i]=="NUTRITIONAL INFORMATION":

				info=str(soup.select('div#tab_04> table')[0])
				#print(info)
				# table_head = [[cell.text for cell in row("th")]
    #                      for row in BeautifulSoup(info)("tr")]
				table_data = [[cell.text for cell in (row("td") or row("th"))]
                         for row in BeautifulSoup(info,'lxml')("tr")]
				# print (json.dumps(xmltodict.parse(gdp_table_data)))
				# info_list.append(str(info))
				info_list[desc[i].lower().replace(" ","_")]=(table_data)
			else:
				info_list[desc[i].lower().replace(" ","_")]=(info.text.strip())
		except Exception as e:
			pass
			# if not (e == "list index out of range"):
			# 	print(e)

	# append he prodct infromation into the products list
	product_list.append({'name':name, 'price':{"$numberDouble":price}, 'image_list':image_list, 'subcategory':subcategory, 'description':info_list.get("description",""), 'others':{'unit':unit, 'quantity':quantity, 'country':country,  'info_list':info_list, 'scrapped_url':url} })



#write out the products
with open('products.json', 'w') as the_file:
	the_file.write(json.dumps(product_list, indent=4))
# print(json.dumps(product_list, indent=4))









# chrome_options = Options()
# chrome_options.add_argument('--headless')
# # chrome_options.add_argument('--no-sandbox')
# # chrome_options.add_argument('--disable-dev-shm-usage')
# chrome_options.binary_location = r'/mnt/c/Program Files/Mozilla Firefox/firefox.exe'
# browser = webdriver.Firefox(executable_path=r'/opt/WebDriver/bin/geckodriver', firefox_options=chrome_options)



# browser.get("https://www.kibsons.com/shopping/CategoryProducts?searchType=CATEGORY&searchText=Dairy&searchcategory=")
# browser.execute_script("window.scrollTo(0,document.body.scrollHeight)")
# time.sleep(3)
# browser.close()






# db.products.aggregate([ {    $search: {      "text": {        "query": "Bostock",        "path": ["name","subcategory","description","others.quantity"]      }    }},{ $project:{name:1, price:1, description:1, score: { $meta: "searchScore" }:1}  }]).pretty()  





# db.products.aggregate([

#   {

#     $search: {

#       "text": {

#         "query": "Bostock",

#         "path": ["name","subcategory","description","others.quantity"] 

#       }

#     }

#   },

#   {

#   	$sort:{
#   	score: -1

#   	}
#   },

#   {

#     $project: {

#       name: 1,

#       price: 1,

#       score: { $meta: "searchScore" },

      

#     }

#   }

# ])