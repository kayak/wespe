Usage - Facebook Business
-------------------------


All steps from now on will assume you've already set the default api connection using facebook_busines. It's also
possible to set one on the fly by providing the api kwarg in FacebookBatchUploader's constructor.


    from wespe.batch_uploaders import FacebookBatchUploader

    # There is no request limit. If necessary Wespe will coordinate the execution of multiple FacebookAdsApiBatch
    # instances.
    batch_uploader = FacebookBatchUploader(requests)

    try:
        batch_uploader.execute()
    except BatchExecutionError:
        for error in batch_uploader.errors:
            # See FacebookBatchRequestError for more info on what you can do
            pass

    for response in batch_uploader.responses:
        # See FacebookBatchResponse for more info on what you can do
        pass
