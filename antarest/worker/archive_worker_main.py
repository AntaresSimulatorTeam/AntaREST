import multiprocessing

if __name__ == "__main__":
    # Freeze support needed for pyinstaller
    multiprocessing.freeze_support()

    from antarest.worker.archive_worker_service import run_archive_worker

    run_archive_worker()
