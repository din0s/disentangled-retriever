from pathlib import Path
import argparse


def download_queries(args):
    import pandas as pd
    import wget, gzip, shutil, os

    csv_file = f"{args.dataset}/queries.csv"
    jsonl_file = f"{args.dataset}/queries.jsonl"
    url = f"https://github.com/castorini/anserini/raw/master/src/main/resources/topics-and-qrels/topics.beir-v1.0.0-{args.pyserini_name}.test.tsv.gz"

    # Download and unzip
    gz_file = f"{csv_file}.gz"
    wget.download(url, gz_file)
    with gzip.open(gz_file, "rb") as f_in:
        with open(csv_file, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(gz_file)

    # Read csv for conversion
    df = pd.read_csv(
        csv_file,
        sep="^([^\t]+)\t",
        engine="python",
        header=None,
        usecols=[1, 2],
        names=["_id", "text"],
    )

    # Fix for robust04
    if args.pyserini_name == "robust04":
        df["text"] = df["text"].str.split().str.join(" ")

    # Add metadata column
    df["metadata"] = [{} for _ in range(len(df))]

    # Save to disk as jsonl
    df.to_json(jsonl_file, orient="records", lines=True)

    # Cleanup
    os.remove(csv_file)


def download_qrels(args):
    import pandas as pd
    import wget, os

    dir = f"{args.dataset}/qrels"
    os.makedirs(dir, exist_ok=True)

    ssv_file = f"{dir}/test.ssv"
    tsv_file = f"{dir}/test.tsv"
    url = f"https://github.com/castorini/anserini/raw/master/src/main/resources/topics-and-qrels/qrels.beir-v1.0.0-{args.pyserini_name}.test.txt"

    # Download
    wget.download(url, ssv_file)

    # Read ssv for conversion
    df = pd.read_csv(
        ssv_file,
        sep=" ",
        header=None,
        usecols=[0, 2, 3],
        names=["query-id", "corpus-id", "score"],
    )

    # Save to disk as tsv
    df.to_csv(tsv_file, sep="\t", index=False)

    # Cleanup
    os.remove(ssv_file)


def download_corpus(args):
    from pyserini.search import LuceneSearcher
    import json

    jsonl_file = f"{args.dataset}/corpus.jsonl"

    # (Down)Load pyserini index
    index_name = f"beir-v1.0.0-{args.pyserini_name}-flat"
    searcher = LuceneSearcher.from_prebuilt_index(index_name)

    # Convert to jsonl
    with open(jsonl_file, "w") as writer:
        for i in range(searcher.num_docs):
            doc = searcher.doc(i).raw()
            doc = json.dumps(json.loads(doc))  # get rid of spaces
            writer.write(doc + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--pyserini_name", type=str)
    parser.add_argument("--download_all", action="store_true", default=False)
    parser.add_argument("--download_queries", action="store_true", default=False)
    parser.add_argument("--download_qrels", action="store_true", default=False)
    parser.add_argument("--download_corpus", action="store_true", default=False)
    args = parser.parse_args()

    if args.pyserini_name is None:
        args.pyserini_name = args.dataset

    args.download_queries = args.download_all or args.download_queries
    args.download_qrels = args.download_all or args.download_qrels
    args.download_corpus = args.download_all or args.download_corpus

    Path(args.dataset).mkdir(parents=True, exist_ok=True)
    print(f"Downloading {args.dataset}")
    if args.download_queries:
        print()
        print("Downloading queries...")
        download_queries(args)
    if args.download_qrels:
        print()
        print("Downloading qrels...")
        download_qrels(args)
    if args.download_corpus:
        print()
        print("Downloading corpus...")
        download_corpus(args)

