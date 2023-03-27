from common_crawl_corpus import CC_Corpus

if __name__ == "__main__":
    cc = CC_Corpus()
    cc.process_crawl("data_store/CC-MAIN-2022-40/jobs/CC-MAIN-2022-40-wet.paths.gz", "CC-MAIN-2022-40")

