import json
import requests

from pprint import pprint

from . import config
import logging
logger = logging.getLogger(__name__)

SERVER_URL = config.settings.MORIARTY_URL + '/rest/executeWorkFlow/'

TEXT_OPINION_STR = {
    '-1.0': "Muy malo",
    '-0.5': "Malo",
    '0.0': "Neutro",
    '0.5': "Bueno",
    '1.0': "Muy bueno",
}


def call_WF(text):
    url = SERVER_URL + "5a6880245a93535c9a696f03?wait=true"
    data = {'NerBoolean': True,
            'OpinionBoolean': True,
            'inputTextEntrada': text}
    data_json = json.dumps(data)
    headers = {'Content-type': 'application/json'}

    response = requests.post(url, data=data_json, headers=headers)
    return response.json()


def call_WF2(text):
    # WFComplete_HackathonITAINNOVA2
    # url = SERVER_URL + '5a6aeb2b5a93535c9a69d33e?wait=true'

    # WFComplete_HackathonITAINNOVA3
    url = SERVER_URL + '5a74307d5a93535c9a6cd5b3?wait=true'

    # text_length = len(text)
    # if text_length < 50:
    #     wordsMin = 0
    #     wordsMax = 0
    #     summarizer = False
    # else:
    #     wordsMin = text_length // 4
    #     wordsMax = text_length // 2
    #     summarizer = True
    wordsMin = 10
    wordsMax = 30

    data = {
        'NerBoolean': True,
        'OpinionBoolean': True,
        'SummarizerBoolean': True,
        'wordsMin': wordsMin,
        'wordsMax': wordsMax,
        'algorithm': 'rank',
        'inputTextEntrada': text,
        'tags': 'CDPQO',
    }
    data_json = json.dumps(data)
    headers = {'Content-type': 'application/json'}

    try:
        logger.info("Sending Moriarty post request...")
        response = requests.post(url, data=data_json, headers=headers)
        logger.debug("Moriarty request response code: {}".format(response.status_code))

        response.raise_for_status()
        results = response.json()['results']
        logger.debug(results)
    except requests.HTTPError:
        logger.exception("Moriarty WF request failed with status code {}".format(response.status_code))
        logger.debug("for text: " + text)
    except requests.ConnectionError as e:
        logger.error("Moriarty WF request failed: {}".format(e))
    except requests.RequestException:
        logger.exception("Moriarty WF request failed")
    except TypeError:
        logger.error("Moriarty WF results json parse failed")
        logger.error(response.text)
    else:
        try:
            if results['language'] == 'Spanish':
                return {
                    'places': results['localizacionesList'],
                    'organizations': results['organizacionesList'],
                    'people': results['personasList'],
                    'textOpinion': results['opinion'],
                    'textOpinionStr': TEXT_OPINION_STR[results['opinion']],
                    'summary': results['summarizedText'],
                    'textProcessed': results.get('textProcessed')
                }
        except KeyError:
            logger.exception("Moriarty failed")
            logger.error(response.json()['message'])
            logger.debug(response.json()['message'])


if __name__ == '__main__':
    # logging.basicConfig(level=logging.WARNING, format='%(asctime)s ' + logging.BASIC_FORMAT)
    # Test text
    print(call_WF2("El oeste de Texas divide la frontera entre Mexico y Nuevo México. "
                   "Es muy bella pero aspera, llena de cactus, en esta region se encuentran las Davis Mountains. "
                   "Todo el terreno esta lleno de piedra caliza, torcidos arboles de mezquite y espinosos nopales. "
                   "Para admirar la verdadera belleza desertica, visite el Parque Nacional de Big Bend, "
                   "cerca de Brownsville. Es el lugar favorito para los excurcionistas, acampadores y entusiastas "
                   "de las rocas. Pequeños pueblos y ranchos se encuentran a lo largo de las planicies y cañones "
                   "de esta region. El area solo tiene dos estaciones, tibia y realmente caliente. La mejor epoca "
                   "para visitarla es de Diciembre a Marzo cuando los dias son tibios, las noches son frescas y "
                   "florecen las plantas del desierto con la humedad en el aire."))
