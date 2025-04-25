import logging
import concurrent.futures

#! import sentence_transformers

class SentenceTransformerEmbedder:

    def __init__(self,tbatch_size = 32, processing_type = 'batch', max_workers = 2, *args, **kwargs):
        # Suppress SentenceTransformer logging

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            print("Please install `sentence_transformers` to use this feature.")
            print(e)

        logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
        self.tbatch_size = tbatch_size
        self.processing_type = processing_type
        self.max_workers = max_workers
        self.model = SentenceTransformer(*args, **kwargs)

    def embed_sentence_transformer(self, text):

        """
        Embeds single query with sentence tranformer embedder.
        """

        return self.model.encode(text)

    def embed(self, text, processing_type : str = None):

        """
        Embeds single query with sentence with selected embedder.
        """

        if processing_type is None:
            processing_type = self.processing_type

        if processing_type == 'batch':
           return self.embed_texts_in_batches(texts = text)

        if processing_type == 'parallel':
           return self.embed_sentences_in_batches_parallel(texts = text)

        return self.embed_sentence_transformer(text = str(text))

    def embed_texts_in_batches(self, texts, batch_size : int = None):
        """
        Embeds a list of texts in batches.
        """
        if batch_size is None:
            batch_size = self.tbatch_size

        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.model.encode(batch, show_progress_bar=False)
            embeddings.extend(batch_embeddings)
        return embeddings

    def embed_sentences_in_batches_parallel(self, texts, batch_size: int = None, max_workers: int = None):
        """
        Embeds a list of texts in batches in parallel using processes.
        """

        if batch_size is None:
            batch_size = self.tbatch_size

        if max_workers is None:
            max_workers = self.max_workers

        batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]

        embeddings = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            future_to_batch = {executor.submit(self.embed_sentence_transformer, batch): batch for batch in batches}

            for future in concurrent.futures.as_completed(future_to_batch):
                embeddings.extend(future.result())

        return embeddings