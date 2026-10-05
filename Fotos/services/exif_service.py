from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS, IFD


class ExifService:
    @staticmethod
    def converte_coordenada_em_decimal(G,M,S,PC):
        coordenada_decimal = G + ((M/60) + (S/3600))

        coordenada_decimal = (
         -coordenada_decimal
          if PC.upper() in ["S", "W"]
            else coordenada_decimal)
        return round(float(coordenada_decimal), 6)


    @staticmethod
    def extrair_exif(arquivo):
      with Image.open(arquivo) as img:
        exif = img.getexif()
        if not exif:
         print ("Não existem metadados neste arquivo.")
         return None
        return exif

    @staticmethod
    def extrair_gps(exif):
        if exif:
            gps_ifd = exif.get_ifd(IFD.GPSInfo)

            if not gps_ifd:
                return None

            gps = {}

            for tag_id, valor in gps_ifd.items():
                nome_tag = GPSTAGS.get(tag_id, tag_id)
                gps[nome_tag] = valor


            return gps
        return None

    @staticmethod
    def extrair_coordenadas(gps):
        if not gps:
            return None

        latitude = gps.get("GPSLatitude")
        latitude_ref = gps.get("GPSLatitudeRef")

        longitude = gps.get("GPSLongitude")
        longitude_ref = gps.get("GPSLongitudeRef")

        if not latitude or not latitude_ref or not longitude or not longitude_ref:
            return None

        lat_graus, lat_minutos, lat_segundos = latitude
        lon_graus, lon_minutos, lon_segundos = longitude

        latitude_decimal = ExifService.converte_coordenada_em_decimal(
            lat_graus,
            lat_minutos,
            lat_segundos,
            latitude_ref
        )

        longitude_decimal = ExifService.converte_coordenada_em_decimal(
            lon_graus,
            lon_minutos,
            lon_segundos,
            longitude_ref
        )

        return {
            "latitude": latitude_decimal,
            "longitude": longitude_decimal
        }


    @staticmethod
    def obter_localizacao(arquivo):
        exif = ExifService.extrair_exif(arquivo)
        if not exif:
            return None

        gps = ExifService.extrair_gps(exif)
        if not gps:
            return None
        coordenadas = ExifService.extrair_coordenadas(gps)
        if not coordenadas:
            return None

        return coordenadas