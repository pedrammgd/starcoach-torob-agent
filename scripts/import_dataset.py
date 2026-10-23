from pathlib import Path
import csv,json,hashlib,collections
import argparse
parser=argparse.ArgumentParser();parser.add_argument('dataset',type=Path);args=parser.parse_args()
R=Path(__file__).resolve().parent.parent;S=args.dataset;D=R/'docs';D.mkdir(exist_ok=True)
shops={};counts={};hashes={}
for name in ['shops','offers','products']:
 p=S/(name+'.csv');hashes[name]=hashlib.sha256(p.read_bytes()).hexdigest()
with (S/'shops.csv').open(encoding='utf-8-sig',newline='') as h:
 for r in csv.DictReader(h):
  try:lat,lon=float(r['lat']),float(r['lon'])
  except (ValueError,TypeError):continue
  if not(34<lat<37 and 50<lon<53):continue
  shops[r['shop_id']]={k:r[k] for k in ['shop_id','name','address','location_label','weekly_hours','payment_options']};shops[r['shop_id']].update(lat=lat,lon=lon)
counts['shops_with_valid_coordinates']=len(shops)
offers=collections.defaultdict(list);n=0
with (S/'offers.csv').open(encoding='utf-8-sig',newline='') as h:
 for r in csv.DictReader(h):
  n+=1
  try:price=int(r['price_toman'])
  except (ValueError,TypeError):continue
  if r['shop_id'] not in shops or price<=0:continue
  offers[r['product_id']].append({k:r[k] for k in ['offer_id','shop_id','last_price_changed_at','warranty']}|{'price':price})
counts['offers_source']=n
products=[];n=0
with (S/'products.csv').open(encoding='utf-8-sig',newline='') as h:
 for r in csv.DictReader(h):
  n+=1
  if len(products)<1800 and len({o['shop_id'] for o in offers.get(r['product_id'],[])})>=2:
   products.append({k:r[k] for k in ['product_id','persian_title','brand_name','category_name']}|{'offers':offers[r['product_id']]})
counts['products_source']=n
used={o['shop_id'] for p in products for o in p['offers']};data={'products':products,'shops':{k:shops[k] for k in used},'source':'starcoach-dataset-v16-cap300-csv','historical_prices':True,'inventory_verified':False}
(D/'data.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
evidence={'source_folder_basename':S.name,'source_sha256':hashes,'counts':counts,'public_products':len(products),'public_offers':sum(len(p['offers']) for p in products),'public_shops':len(used),'selection':'first1800 source-order products with offers from at least2 distinct shops and valid shop coordinates','contacts_excluded':True,'historical_prices':True,'inventory_verified':False,'shop_names_mostly_synthetic_in_official_dataset':True,'four_video_stages_verified':False}
(R/'DATASET_EVIDENCE.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n');print(json.dumps(evidence,ensure_ascii=False))
