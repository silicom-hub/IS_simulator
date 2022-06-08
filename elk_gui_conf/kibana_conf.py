import os
import json
import random
import requests

header_elastic = {"Content-Type":"application/json", "kbn-xsrf":"true"}

#### Get indices
alias = requests.get("http://127.0.0.1:9200/_alias").json()
for indice in alias.keys():
    if indice[0] != ".":
        data = '{"attributes":{"title":"'+indice+'","timeFieldName":"@timestamp"}}'
        print(requests.post("http://127.0.0.1:5601/api/saved_objects/index-pattern/"+indice+"?overwrite=true", headers=header_elastic, data=data))
    if "hacker" in indice:
        export_file = open("hacker.ndjson")
        export_string = export_file.read().replace("my_index_pattern", indice).replace("my_id", indice)
        export_file.close()
        new_export_file = open("new_"+indice+".ndjson", "w")
        new_export_file.write(export_string)
        new_export_file.close()
        os.system('curl -X POST http://127.0.0.1:5601/api/saved_objects/_import?overwrite=true -H "kbn-xsrf: true" --form file=@new_'+indice+'.ndjson')
    if "mail" in indice:
        export_file = open("mail.ndjson")
        export_string = export_file.read().replace("my_index_pattern", indice).replace("my_title", indice).replace("my_id", indice)
        export_file.close()
        new_export_file = open("new_"+indice+".ndjson", "w")
        new_export_file.write(export_string)
        new_export_file.close()
        os.system('curl -X POST http://127.0.0.1:5601/api/saved_objects/_import?overwrite=true -H "kbn-xsrf: true" --form file=@new_'+indice+'.ndjson')
    if "apache2_access" in indice:
        export_file = open("apache.ndjson")
        export_string = export_file.read().replace("my_index_pattern", indice).replace("my_title", indice).replace("my_id", indice)
        export_file.close()
        new_export_file = open("new_"+indice+".ndjson", "w")
        new_export_file.write(export_string)
        new_export_file.close()
        os.system('curl -X POST http://127.0.0.1:5601/api/saved_objects/_import?overwrite=true -H "kbn-xsrf: true" --form file=@new_'+indice+'.ndjson')
