import hackathon
import time

TEXTO_PRUEBA = ("El oeste de Texas divide la frontera entre Mexico y Nuevo México. "
                "Es muy bella pero aspera, llena de cactus, en esta region se encuentran las Davis Mountains. "
                "Todo el terreno esta lleno de piedra caliza, torcidos arboles de mezquite y espinosos nopales. "
                "Para admirar la verdadera belleza desertica, visite el Parque Nacional de Big Bend, "
                "cerca de Brownsville. Es el lugar favorito para los excurcionistas, acampadores y entusiastas "
                "de las rocas. Pequeños pueblos y ranchos se encuentran a lo largo de las planicies y cañones "
                "de esta region. El area solo tiene dos estaciones, tibia y realmente caliente. La mejor epoca "
                "para visitarla es de Diciembre a Marzo cuando los dias son tibios, las noches son frescas y "
                "florecen las plantas del desierto con la humedad en el aire.")

if __name__ == '__main__':
    # hackathon.process_all_docs()

    # print("Task going to sleep")
    # time.sleep(60 * 60)

    # print("Task awoken")
    # hackathon.solr.delete_all()

    # hackathon.periodic_task()

    hackathon.call_WF.call_WF2(TEXTO_PRUEBA)
