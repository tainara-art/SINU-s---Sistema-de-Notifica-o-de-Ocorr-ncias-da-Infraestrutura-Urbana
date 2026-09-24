from PIL import Image
from PIL.ExifTags import TAGS

class ExifService:
    @staticmethod
    def converte_coordenada_em_decimal(G,M,S,PC):
        coordenada_decimal = G + ((M/60) + (S/3600))

        coordenada_decimal = (
         -coordenada_decimal
          if PC.upper() in ["S", "W"]
            else coordenada_decimal)
        return round(coordenada_decimal, 6)

    @staticmethod
    def extrair_exif(arquivo):
      with Image.open(arquivo) as img:
        exif = img.getexif()
        if not exif:
         print ("Não existem metadados neste arquivo.")
         return None
        return exif

            
                
