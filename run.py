import hackathon
import time

if __name__ == '__main__':
    # hackathon.process_all_docs()

    print("Task going to sleep")
    time.sleep(60 * 60)

    print("Task awoken")
    hackathon.solr.delete_all()
    hackathon.periodic_task()
