import multiprocessing

if __name__ == "__main__":
    # Freeze support needed for pyinstaller. Important to run it before other imports,
    # because some of them call multiprocessing functions.
    multiprocessing.freeze_support()

    from antarest.worker.archive_worker_service import run_archive_worker

    run_archive_worker()
