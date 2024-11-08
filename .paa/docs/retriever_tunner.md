# Retriever tunner

A simple tool to compare and tune retriever performance, given a desired ranking to strive for. 
The goal is to provide a simple metric to measure how a given retriever is close to the 'ideal', generated for example
with a use of more expensive, slower or simply no-existant method. 


```python
import sys
sys.path.append('../')
from python_modules.retriever_tunner import RetrieverTunner
```

### 1. Downloading test data


```python
import nltk
from nltk.corpus import brown

# Download the necessary datasets from NLTK
nltk.download('brown')
nltk.download('punkt')

# Load the Brown Corpus as plain text
brown_corpus_text = ' '.join(brown.words())

# Split the corpus into sentences
sentences = nltk.sent_tokenize(brown_corpus_text)

# Display the number of sentences and first few sentences as a sample
print(f"Number of sentences: {len(sentences)}")
print("First few sentences:")
for sentence in sentences[:5]:
    print(sentence)
```

    [nltk_data] Downloading package brown to /home/runner/nltk_data...
    [nltk_data]   Unzipping corpora/brown.zip.
    [nltk_data] Downloading package punkt to /home/runner/nltk_data...


    [nltk_data]   Unzipping tokenizers/punkt.zip.


    Number of sentences: 56601
    First few sentences:
    The Fulton County Grand Jury said Friday an investigation of Atlanta's recent primary election produced `` no evidence '' that any irregularities took place .
    The jury further said in term-end presentments that the City Executive Committee , which had over-all charge of the election , `` deserves the praise and thanks of the City of Atlanta '' for the manner in which the election was conducted .
    The September-October term jury had been charged by Fulton Superior Court Judge Durwood Pye to investigate reports of possible `` irregularities '' in the hard-fought primary which was won by Mayor-nominate Ivan Allen Jr. .
    `` Only a relative handful of such reports was received '' , the jury said , `` considering the widespread interest in the election , the number of voters and the size of this city '' .
    The jury said it did find that many of Georgia's registration and election laws `` are outmoded or inadequate and often ambiguous '' .


### 2. Initialize RetrieverTunner


```python
rt = RetrieverTunner(
    # optional/ required
    search_values_list = sentences[0:2000],
    target_ranking_name = 'all-mpnet-base-v2',
    embedding_model_names = ['paraphrase-multilingual-mpnet-base-v2',
                             'all-mpnet-base-v2', 
                             'multi-qa-mpnet-base-dot-v1', 
                             'all-MiniLM-L6-v2'],
    # optional
    similarity_search_h_params = {'processing_type' : 'parallel',
                                                  'max_workers' : 8,
                                                   'tbatch_size' : 1000},
    n_random_queries = 100,
    seed = 23,
    metrics_params = {'n_results' : [1,3,5,10],   
                      'ceilings' : [10],
                      'prep_types' : ['correction', 'ceiling'],
                      'weights_ratio' : 0.6,
                      'weights_sum' : 1,
                      'inverted' : True},
    # for plotting
    plots_params = {'top_n' : 3,
                    'text_lim' : 10,
                    'alpha' : 0.5,
                    'save_comp_plot' : False}
    )

```


    .gitattributes:   0%|          | 0.00/690 [00:00<?, ?B/s]



    1_Pooling/config.json:   0%|          | 0.00/190 [00:00<?, ?B/s]



    README.md:   0%|          | 0.00/4.10k [00:00<?, ?B/s]



    config.json:   0%|          | 0.00/723 [00:00<?, ?B/s]



    config_sentence_transformers.json:   0%|          | 0.00/122 [00:00<?, ?B/s]



    pytorch_model.bin:   0%|          | 0.00/1.11G [00:00<?, ?B/s]



    sentence_bert_config.json:   0%|          | 0.00/53.0 [00:00<?, ?B/s]



    sentencepiece.bpe.model:   0%|          | 0.00/5.07M [00:00<?, ?B/s]



    special_tokens_map.json:   0%|          | 0.00/239 [00:00<?, ?B/s]



    tokenizer.json:   0%|          | 0.00/9.08M [00:00<?, ?B/s]



    tokenizer_config.json:   0%|          | 0.00/402 [00:00<?, ?B/s]



    modules.json:   0%|          | 0.00/229 [00:00<?, ?B/s]



    .gitattributes:   0%|          | 0.00/1.18k [00:00<?, ?B/s]



    1_Pooling/config.json:   0%|          | 0.00/190 [00:00<?, ?B/s]



    README.md:   0%|          | 0.00/10.6k [00:00<?, ?B/s]



    config.json:   0%|          | 0.00/571 [00:00<?, ?B/s]



    config_sentence_transformers.json:   0%|          | 0.00/116 [00:00<?, ?B/s]



    data_config.json:   0%|          | 0.00/39.3k [00:00<?, ?B/s]



    pytorch_model.bin:   0%|          | 0.00/438M [00:00<?, ?B/s]



    sentence_bert_config.json:   0%|          | 0.00/53.0 [00:00<?, ?B/s]



    special_tokens_map.json:   0%|          | 0.00/239 [00:00<?, ?B/s]



    tokenizer.json:   0%|          | 0.00/466k [00:00<?, ?B/s]



    tokenizer_config.json:   0%|          | 0.00/363 [00:00<?, ?B/s]



    train_script.py:   0%|          | 0.00/13.1k [00:00<?, ?B/s]



    vocab.txt:   0%|          | 0.00/232k [00:00<?, ?B/s]



    modules.json:   0%|          | 0.00/349 [00:00<?, ?B/s]



    .gitattributes:   0%|          | 0.00/737 [00:00<?, ?B/s]



    1_Pooling/config.json:   0%|          | 0.00/190 [00:00<?, ?B/s]



    README.md:   0%|          | 0.00/8.66k [00:00<?, ?B/s]



    config.json:   0%|          | 0.00/571 [00:00<?, ?B/s]



    config_sentence_transformers.json:   0%|          | 0.00/116 [00:00<?, ?B/s]



    data_config.json:   0%|          | 0.00/25.5k [00:00<?, ?B/s]



    pytorch_model.bin:   0%|          | 0.00/438M [00:00<?, ?B/s]



    sentence_bert_config.json:   0%|          | 0.00/53.0 [00:00<?, ?B/s]



    special_tokens_map.json:   0%|          | 0.00/239 [00:00<?, ?B/s]



    tokenizer.json:   0%|          | 0.00/466k [00:00<?, ?B/s]



    tokenizer_config.json:   0%|          | 0.00/363 [00:00<?, ?B/s]



    train_script.py:   0%|          | 0.00/13.9k [00:00<?, ?B/s]



    vocab.txt:   0%|          | 0.00/232k [00:00<?, ?B/s]



    modules.json:   0%|          | 0.00/229 [00:00<?, ?B/s]



    .gitattributes:   0%|          | 0.00/1.18k [00:00<?, ?B/s]



    1_Pooling/config.json:   0%|          | 0.00/190 [00:00<?, ?B/s]



    README.md:   0%|          | 0.00/10.6k [00:00<?, ?B/s]



    config.json:   0%|          | 0.00/612 [00:00<?, ?B/s]



    config_sentence_transformers.json:   0%|          | 0.00/116 [00:00<?, ?B/s]



    data_config.json:   0%|          | 0.00/39.3k [00:00<?, ?B/s]



    pytorch_model.bin:   0%|          | 0.00/90.9M [00:00<?, ?B/s]



    sentence_bert_config.json:   0%|          | 0.00/53.0 [00:00<?, ?B/s]



    special_tokens_map.json:   0%|          | 0.00/112 [00:00<?, ?B/s]



    tokenizer.json:   0%|          | 0.00/466k [00:00<?, ?B/s]



    tokenizer_config.json:   0%|          | 0.00/350 [00:00<?, ?B/s]



    train_script.py:   0%|          | 0.00/13.2k [00:00<?, ?B/s]



    vocab.txt:   0%|          | 0.00/232k [00:00<?, ?B/s]



    modules.json:   0%|          | 0.00/349 [00:00<?, ?B/s]


### 3. Construct ranking


```python
rt.construct_rankings(
    # optional
    queries = rt.queries,
    queries_filters = None,
    search_values_dicts = None,
    search_values_list = rt.search_values_list,
    model_names = rt.embedding_model_names,
    handlers = rt.sim_search_handlers
)
```

### 4. Make scores


```python
rt.make_scores_dict(
    # optional
    target_ranking = rt.ranking_dicts[rt.target_ranking_name],
    compared_rankings = {ranking : rt.ranking_dicts[ranking] for ranking in rt.embedding_model_names \
                if ranking != rt.target_ranking_name},
    n_results = [1,2], 
    ceilings=[], 
    prep_types=['correction'],
    weights_ratio=0.8, # weight skewed to right
    weights_sum = rt.metrics_params['weights_sum'],
    inverted = True)
```




    {'all-mpnet-base-v2|paraphrase-multilingual-mpnet-base-v2': {'rdm|1|100|correction': 1.0,
      'rdm|2|100|correction': 0.5072,
      'rdm|100|100|correction': 0.0},
     'all-mpnet-base-v2|multi-qa-mpnet-base-dot-v1': {'rdm|1|100|correction': 1.0,
      'rdm|2|100|correction': 0.5348,
      'rdm|100|100|correction': 0.0},
     'all-mpnet-base-v2|all-MiniLM-L6-v2': {'rdm|1|100|correction': 0.99,
      'rdm|2|100|correction': 0.5136000000000001,
      'rdm|100|100|correction': 0.0}}



### 5. Plot rankings


```python
rt.show_model_comparison_plot(
    # optional
    ranking_dicts = rt.ranking_dicts,
    target_model = rt.target_ranking_name,
    compared_model = 'paraphrase-multilingual-mpnet-base-v2',
    top_n = 3, 
    alpha = 0.5,
    text_lim = rt.plots_params['text_lim']
    )
```


        <script type="text/javascript">
        window.PlotlyConfig = {MathJaxConfig: 'local'};
        if (window.MathJax && window.MathJax.Hub && window.MathJax.Hub.Config) {window.MathJax.Hub.Config({SVG: {font: "STIX-Web"}});}
        if (typeof require !== 'undefined') {
        require.undef("plotly");
        define('plotly', function(require, exports, module) {
            /**
* plotly.js v2.27.0
* Copyright 2012-2023, Plotly, Inc.
* All rights reserved.
* Licensed under the MIT license
*/
/*! For license information please see plotly.min.js.LICENSE.txt */
        });
        require(['plotly'], function(Plotly) {
            window._Plotly = Plotly;
        });
        }
        </script>




<div>                            <div id="35f5c36b-d362-46ff-b715-2b0c257c80fa" class="plotly-graph-div" style="height:525px; width:100%;"></div>            <script type="text/javascript">                require(["plotly"], function(Plotly) {                    window.PLOTLYENV=window.PLOTLYENV || {};                                    if (document.getElementById("35f5c36b-d362-46ff-b715-2b0c257c80fa")) {                    Plotly.newPlot(                        "35f5c36b-d362-46ff-b715-2b0c257c80fa",                        [{"marker":{"opacity":0.5},"mode":"markers","name":"He said th","x":[894,874,870],"y":[894,874,870],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` Usually","x":[596,592,601],"y":[596,592,695],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Robinson t","x":[942,943,939],"y":[942,943,944],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` I'm a m","x":[1593,1592,1913],"y":[1593,1592,1912],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Each had b","x":[827,786,1747],"y":[827,284,1079],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mrs. Arthu","x":[699,727,631],"y":[699,727,726],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Dr. Clark ","x":[1171,1167,1170],"y":[1171,1167,1170],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Aj .","x":[1034,836,632],"y":[1034,573,756],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Gauer work","x":[212,276,282],"y":[212,474,1543],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The three ","x":[1628,1618,1630],"y":[1628,1618,1630],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Last week ","x":[1867,1868,1845],"y":[1867,1868,1894],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Backs high","x":[1776,1764,1763],"y":[1776,1763,1778],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` Our int","x":[85,86,88],"y":[85,86,101],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Managing D","x":[1733,1537,1529],"y":[1733,1846,1819],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Legislator","x":[1266,1223,1269],"y":[1266,1223,1240],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Miss Burke","x":[486,474,480],"y":[486,485,480],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The only d","x":[1393,1392,1396],"y":[1393,1396,192],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The Mayor ","x":[1547,316,1545],"y":[1547,1532,1643],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"A capsule ","x":[1910,1907,1912],"y":[1910,1907,1912],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"They have ","x":[1028,446,655],"y":[1028,742,446],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Regrets at","x":[1452,1465,1441],"y":[1452,1469,1465],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"A couple o","x":[270,311,266],"y":[270,8,9],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Three were","x":[1931,1973,1936],"y":[1931,1973,1936],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"From the o","x":[846,845,1271],"y":[846,845,1273],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He will be","x":[1050,209,1039],"y":[1050,1166,1051],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Wexler had","x":[1216,1208,1209],"y":[1216,1209,1220],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Chester O.","x":[1175,741,828],"y":[1175,959,505],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mrs. Henry","x":[454,668,579],"y":[454,579,668],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"I never di","x":[20,19,53],"y":[20,19,23],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"On Friday ","x":[1862,1828,1863],"y":[1862,1828,1863],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Georgia Re","x":[1040,1046,1044],"y":[1040,1042,1046],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` He knoc","x":[49,120,387],"y":[49,281,282],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"So he woun","x":[285,297,286],"y":[285,270,297],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He's been ","x":[503,809,502],"y":[503,64,809],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The change","x":[1883,1884,1882],"y":[1883,1887,1005],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Concern ba","x":[1735,1736,1512],"y":[1735,1736,1740],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mrs. Roger","x":[578,744,645],"y":[578,744,755],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"While deta","x":[1117,1116,1418],"y":[1117,1116,1143],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He assured","x":[1421,1385,1855],"y":[1421,1416,1414],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"In another","x":[603,605,602],"y":[603,602,610],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Barber , w","x":[1072,1074,1071],"y":[1072,1074,1570],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Only Bucky","x":[206,205,177],"y":[206,178,414],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"know enoug","x":[1755,1749,1752],"y":[1755,1752,1749],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"After a le","x":[347,346,349],"y":[347,346,349],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"His sense ","x":[1352,1346,1350],"y":[1352,1346,1348],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"It made hi","x":[271,275,324],"y":[271,156,1449],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"It was gre","x":[1442,1857,1275],"y":[1442,1648,1857],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Services t","x":[988,987,998],"y":[988,487,987],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"As we bull","x":[505,436,629],"y":[505,436,485],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The contra","x":[1742,1743,1729],"y":[1742,1741,1743],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He said he","x":[158,157,150],"y":[158,1073,1538],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Gene Marsh","x":[556,553,340],"y":[556,553,247],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"When the A","x":[761,645,661],"y":[761,489,705],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Some 30 sp","x":[983,984,1217],"y":[983,978,979],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Yes , with","x":[171,1880,580],"y":[171,719,727],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The educat","x":[1576,1580,1139],"y":[1576,1580,1139],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` Lindy M","x":[352,355,362],"y":[352,362,1937],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Kowalski ,","x":[996,824,998],"y":[996,998,941],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"But from a","x":[1643,673,1306],"y":[1643,1666,1101],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"I remember","x":[173,418,133],"y":[173,23,194],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The women ","x":[667,753,721],"y":[667,690,452],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The 22-yea","x":[1970,1172,1953],"y":[1970,108,1956],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Along with","x":[1363,1374,1354],"y":[1363,1374,1354],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"!","x":[1601,531,470],"y":[1601,470,521],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"She was mo","x":[1989,258,1256],"y":[1989,1256,258],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He succeed","x":[209,1050,1039],"y":[209,226,220],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Some even ","x":[620,619,610],"y":[620,619,610],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Denials we","x":[1916,1915,1203],"y":[1916,1191,1917],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"They knew ","x":[383,382,917],"y":[383,1758,45],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Asked Palm","x":[315,1449,273],"y":[315,1449,323],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"And after ","x":[1335,1334,1024],"y":[1335,1621,1334],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mr. Hawksl","x":[1372,1369,1623],"y":[1372,1369,1364],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Miss Joan ","x":[636,653,637],"y":[636,653,637],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"One advant","x":[1365,1354,1359],"y":[1365,1354,1457],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He was cal","x":[92,277,23],"y":[92,182,19],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Division s","x":[1662,1661,1659],"y":[1662,1661,1295],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The most v","x":[379,380,262],"y":[379,387,1944],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"We've been","x":[670,70,69],"y":[670,70,69],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Rice has n","x":[65,60,73],"y":[65,13,73],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He suggest","x":[1400,1043,1520],"y":[1400,1083,1485],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"There are ","x":[192,1565,1430],"y":[192,70,1393],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Nursing ho","x":[1234,1235,1236],"y":[1234,1236,1235],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He also re","x":[1168,1634,1828],"y":[1168,1167,1171],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Decisions ","x":[1201,1202,1200],"y":[1201,1202,1908],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Other spea","x":[1872,265,1870],"y":[1872,580,265],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Ordinary C","x":[1079,1088,1087],"y":[1079,1088,1087],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Just when ","x":[163,412,186],"y":[163,186,165],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"An assista","x":[1564,1388,1351],"y":[1564,1652,1825],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"They , on ","x":[925,924,932],"y":[925,924,932],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The $6,100","x":[1574,1568,1514],"y":[1574,1568,1514],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"But we hav","x":[680,676,684],"y":[680,676,684],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Skorich re","x":[208,220,771],"y":[208,220,227],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Districts ","x":[1677,1679,1721],"y":[1677,1679,1717],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The aged c","x":[1223,1266,1221],"y":[1223,1266,1239],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` We want","x":[1757,1759,1758],"y":[1757,1758,1759],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Now 38 , M","x":[843,845,842],"y":[843,845,842],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The U. S. ","x":[1590,1591,1575],"y":[1590,1591,1842],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Dick McAul","x":[110,114,111],"y":[110,114,111],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Tactics st","x":[1624,1304,1298],"y":[1624,1293,1298],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Her husban","x":[832,831,794],"y":[832,831,971],"type":"scatter"}],                        {"template":{"data":{"histogram2dcontour":[{"type":"histogram2dcontour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"choropleth":[{"type":"choropleth","colorbar":{"outlinewidth":0,"ticks":""}}],"histogram2d":[{"type":"histogram2d","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmap":[{"type":"heatmap","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmapgl":[{"type":"heatmapgl","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"contourcarpet":[{"type":"contourcarpet","colorbar":{"outlinewidth":0,"ticks":""}}],"contour":[{"type":"contour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"surface":[{"type":"surface","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"mesh3d":[{"type":"mesh3d","colorbar":{"outlinewidth":0,"ticks":""}}],"scatter":[{"fillpattern":{"fillmode":"overlay","size":10,"solidity":0.2},"type":"scatter"}],"parcoords":[{"type":"parcoords","line":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolargl":[{"type":"scatterpolargl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"bar":[{"error_x":{"color":"#2a3f5f"},"error_y":{"color":"#2a3f5f"},"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"scattergeo":[{"type":"scattergeo","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolar":[{"type":"scatterpolar","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"scattergl":[{"type":"scattergl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatter3d":[{"type":"scatter3d","line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattermapbox":[{"type":"scattermapbox","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterternary":[{"type":"scatterternary","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattercarpet":[{"type":"scattercarpet","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"carpet":[{"aaxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"baxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"type":"carpet"}],"table":[{"cells":{"fill":{"color":"#EBF0F8"},"line":{"color":"white"}},"header":{"fill":{"color":"#C8D4E3"},"line":{"color":"white"}},"type":"table"}],"barpolar":[{"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"pie":[{"automargin":true,"type":"pie"}]},"layout":{"autotypenumbers":"strict","colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#2a3f5f"},"hovermode":"closest","hoverlabel":{"align":"left"},"paper_bgcolor":"white","plot_bgcolor":"#E5ECF6","polar":{"bgcolor":"#E5ECF6","angularaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"radialaxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"ternary":{"bgcolor":"#E5ECF6","aaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"baxis":{"gridcolor":"white","linecolor":"white","ticks":""},"caxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"sequential":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"sequentialminus":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"diverging":[[0,"#8e0152"],[0.1,"#c51b7d"],[0.2,"#de77ae"],[0.3,"#f1b6da"],[0.4,"#fde0ef"],[0.5,"#f7f7f7"],[0.6,"#e6f5d0"],[0.7,"#b8e186"],[0.8,"#7fbc41"],[0.9,"#4d9221"],[1,"#276419"]]},"xaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"yaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"scene":{"xaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"yaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"zaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2}},"shapedefaults":{"line":{"color":"#2a3f5f"}},"annotationdefaults":{"arrowcolor":"#2a3f5f","arrowhead":0,"arrowwidth":1},"geo":{"bgcolor":"white","landcolor":"#E5ECF6","subunitcolor":"white","showland":true,"showlakes":true,"lakecolor":"white"},"title":{"x":0.05},"mapbox":{"style":"light"}}},"xaxis":{"anchor":"y","domain":[0.0,1.0],"title":{"text":"all-mpnet-base-v2"}},"yaxis":{"anchor":"x","domain":[0.0,1.0],"title":{"text":"paraphrase-multilingual-mpnet-base-v2"}},"title":{"text":"Comparison of all-mpnet-base-v2 vs paraphrase-multilingual-mpnet-base-v2"}},                        {"responsive": true}                    ).then(function(){

var gd = document.getElementById('35f5c36b-d362-46ff-b715-2b0c257c80fa');
var x = new MutationObserver(function (mutations, observer) {{
        var display = window.getComputedStyle(gd).display;
        if (!display || display === 'none') {{
            console.log([gd, 'removed!']);
            Plotly.purge(gd);
            observer.disconnect();
        }}
}});

// Listen for the removal of the full notebook cells
var notebookContainer = gd.closest('#notebook-container');
if (notebookContainer) {{
    x.observe(notebookContainer, {childList: true});
}}

// Listen for the clearing of the current output cell
var outputEl = gd.closest('.output');
if (outputEl) {{
    x.observe(outputEl, {childList: true});
}}

                        })                };                });            </script>        </div>



```python
rt.show_model_comparison_plots(
    # optional
    ranking_dicts = rt.ranking_dicts,
    target_model = rt.target_ranking_name,
    compared_models = [model_name for model_name in rt.embedding_model_names \
                if model_name != rt.target_ranking_name],
    top_n = 3, 
    alpha = 0.5,
    text_lim = rt.plots_params['text_lim'])
```


<div>                            <div id="aa5ecdc5-2d06-436d-b634-29e03cd15174" class="plotly-graph-div" style="height:525px; width:100%;"></div>            <script type="text/javascript">                require(["plotly"], function(Plotly) {                    window.PLOTLYENV=window.PLOTLYENV || {};                                    if (document.getElementById("aa5ecdc5-2d06-436d-b634-29e03cd15174")) {                    Plotly.newPlot(                        "aa5ecdc5-2d06-436d-b634-29e03cd15174",                        [{"marker":{"opacity":0.5},"mode":"markers","name":"He said th","x":[894,874,870],"y":[894,874,870],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` Usually","x":[596,592,601],"y":[596,592,695],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Robinson t","x":[942,943,939],"y":[942,943,944],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` I'm a m","x":[1593,1592,1913],"y":[1593,1592,1912],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Each had b","x":[827,786,1747],"y":[827,284,1079],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mrs. Arthu","x":[699,727,631],"y":[699,727,726],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Dr. Clark ","x":[1171,1167,1170],"y":[1171,1167,1170],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Aj .","x":[1034,836,632],"y":[1034,573,756],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Gauer work","x":[212,276,282],"y":[212,474,1543],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The three ","x":[1628,1618,1630],"y":[1628,1618,1630],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Last week ","x":[1867,1868,1845],"y":[1867,1868,1894],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Backs high","x":[1776,1764,1763],"y":[1776,1763,1778],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` Our int","x":[85,86,88],"y":[85,86,101],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Managing D","x":[1733,1537,1529],"y":[1733,1846,1819],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Legislator","x":[1266,1223,1269],"y":[1266,1223,1240],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Miss Burke","x":[486,474,480],"y":[486,485,480],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The only d","x":[1393,1392,1396],"y":[1393,1396,192],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The Mayor ","x":[1547,316,1545],"y":[1547,1532,1643],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"A capsule ","x":[1910,1907,1912],"y":[1910,1907,1912],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"They have ","x":[1028,446,655],"y":[1028,742,446],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Regrets at","x":[1452,1465,1441],"y":[1452,1469,1465],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"A couple o","x":[270,311,266],"y":[270,8,9],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Three were","x":[1931,1973,1936],"y":[1931,1973,1936],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"From the o","x":[846,845,1271],"y":[846,845,1273],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He will be","x":[1050,209,1039],"y":[1050,1166,1051],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Wexler had","x":[1216,1208,1209],"y":[1216,1209,1220],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Chester O.","x":[1175,741,828],"y":[1175,959,505],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mrs. Henry","x":[454,668,579],"y":[454,579,668],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"I never di","x":[20,19,53],"y":[20,19,23],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"On Friday ","x":[1862,1828,1863],"y":[1862,1828,1863],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Georgia Re","x":[1040,1046,1044],"y":[1040,1042,1046],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` He knoc","x":[49,120,387],"y":[49,281,282],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"So he woun","x":[285,297,286],"y":[285,270,297],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He's been ","x":[503,809,502],"y":[503,64,809],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The change","x":[1883,1884,1882],"y":[1883,1887,1005],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Concern ba","x":[1735,1736,1512],"y":[1735,1736,1740],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mrs. Roger","x":[578,744,645],"y":[578,744,755],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"While deta","x":[1117,1116,1418],"y":[1117,1116,1143],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He assured","x":[1421,1385,1855],"y":[1421,1416,1414],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"In another","x":[603,605,602],"y":[603,602,610],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Barber , w","x":[1072,1074,1071],"y":[1072,1074,1570],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Only Bucky","x":[206,205,177],"y":[206,178,414],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"know enoug","x":[1755,1749,1752],"y":[1755,1752,1749],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"After a le","x":[347,346,349],"y":[347,346,349],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"His sense ","x":[1352,1346,1350],"y":[1352,1346,1348],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"It made hi","x":[271,275,324],"y":[271,156,1449],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"It was gre","x":[1442,1857,1275],"y":[1442,1648,1857],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Services t","x":[988,987,998],"y":[988,487,987],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"As we bull","x":[505,436,629],"y":[505,436,485],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The contra","x":[1742,1743,1729],"y":[1742,1741,1743],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He said he","x":[158,157,150],"y":[158,1073,1538],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Gene Marsh","x":[556,553,340],"y":[556,553,247],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"When the A","x":[761,645,661],"y":[761,489,705],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Some 30 sp","x":[983,984,1217],"y":[983,978,979],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Yes , with","x":[171,1880,580],"y":[171,719,727],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The educat","x":[1576,1580,1139],"y":[1576,1580,1139],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` Lindy M","x":[352,355,362],"y":[352,362,1937],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Kowalski ,","x":[996,824,998],"y":[996,998,941],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"But from a","x":[1643,673,1306],"y":[1643,1666,1101],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"I remember","x":[173,418,133],"y":[173,23,194],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The women ","x":[667,753,721],"y":[667,690,452],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The 22-yea","x":[1970,1172,1953],"y":[1970,108,1956],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Along with","x":[1363,1374,1354],"y":[1363,1374,1354],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"!","x":[1601,531,470],"y":[1601,470,521],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"She was mo","x":[1989,258,1256],"y":[1989,1256,258],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He succeed","x":[209,1050,1039],"y":[209,226,220],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Some even ","x":[620,619,610],"y":[620,619,610],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Denials we","x":[1916,1915,1203],"y":[1916,1191,1917],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"They knew ","x":[383,382,917],"y":[383,1758,45],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Asked Palm","x":[315,1449,273],"y":[315,1449,323],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"And after ","x":[1335,1334,1024],"y":[1335,1621,1334],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mr. Hawksl","x":[1372,1369,1623],"y":[1372,1369,1364],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Miss Joan ","x":[636,653,637],"y":[636,653,637],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"One advant","x":[1365,1354,1359],"y":[1365,1354,1457],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He was cal","x":[92,277,23],"y":[92,182,19],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Division s","x":[1662,1661,1659],"y":[1662,1661,1295],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The most v","x":[379,380,262],"y":[379,387,1944],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"We've been","x":[670,70,69],"y":[670,70,69],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Rice has n","x":[65,60,73],"y":[65,13,73],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He suggest","x":[1400,1043,1520],"y":[1400,1083,1485],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"There are ","x":[192,1565,1430],"y":[192,70,1393],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Nursing ho","x":[1234,1235,1236],"y":[1234,1236,1235],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He also re","x":[1168,1634,1828],"y":[1168,1167,1171],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Decisions ","x":[1201,1202,1200],"y":[1201,1202,1908],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Other spea","x":[1872,265,1870],"y":[1872,580,265],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Ordinary C","x":[1079,1088,1087],"y":[1079,1088,1087],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Just when ","x":[163,412,186],"y":[163,186,165],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"An assista","x":[1564,1388,1351],"y":[1564,1652,1825],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"They , on ","x":[925,924,932],"y":[925,924,932],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The $6,100","x":[1574,1568,1514],"y":[1574,1568,1514],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"But we hav","x":[680,676,684],"y":[680,676,684],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Skorich re","x":[208,220,771],"y":[208,220,227],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Districts ","x":[1677,1679,1721],"y":[1677,1679,1717],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The aged c","x":[1223,1266,1221],"y":[1223,1266,1239],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` We want","x":[1757,1759,1758],"y":[1757,1758,1759],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Now 38 , M","x":[843,845,842],"y":[843,845,842],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The U. S. ","x":[1590,1591,1575],"y":[1590,1591,1842],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Dick McAul","x":[110,114,111],"y":[110,114,111],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Tactics st","x":[1624,1304,1298],"y":[1624,1293,1298],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Her husban","x":[832,831,794],"y":[832,831,971],"type":"scatter"}],                        {"template":{"data":{"histogram2dcontour":[{"type":"histogram2dcontour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"choropleth":[{"type":"choropleth","colorbar":{"outlinewidth":0,"ticks":""}}],"histogram2d":[{"type":"histogram2d","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmap":[{"type":"heatmap","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmapgl":[{"type":"heatmapgl","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"contourcarpet":[{"type":"contourcarpet","colorbar":{"outlinewidth":0,"ticks":""}}],"contour":[{"type":"contour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"surface":[{"type":"surface","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"mesh3d":[{"type":"mesh3d","colorbar":{"outlinewidth":0,"ticks":""}}],"scatter":[{"fillpattern":{"fillmode":"overlay","size":10,"solidity":0.2},"type":"scatter"}],"parcoords":[{"type":"parcoords","line":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolargl":[{"type":"scatterpolargl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"bar":[{"error_x":{"color":"#2a3f5f"},"error_y":{"color":"#2a3f5f"},"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"scattergeo":[{"type":"scattergeo","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolar":[{"type":"scatterpolar","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"scattergl":[{"type":"scattergl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatter3d":[{"type":"scatter3d","line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattermapbox":[{"type":"scattermapbox","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterternary":[{"type":"scatterternary","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattercarpet":[{"type":"scattercarpet","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"carpet":[{"aaxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"baxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"type":"carpet"}],"table":[{"cells":{"fill":{"color":"#EBF0F8"},"line":{"color":"white"}},"header":{"fill":{"color":"#C8D4E3"},"line":{"color":"white"}},"type":"table"}],"barpolar":[{"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"pie":[{"automargin":true,"type":"pie"}]},"layout":{"autotypenumbers":"strict","colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#2a3f5f"},"hovermode":"closest","hoverlabel":{"align":"left"},"paper_bgcolor":"white","plot_bgcolor":"#E5ECF6","polar":{"bgcolor":"#E5ECF6","angularaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"radialaxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"ternary":{"bgcolor":"#E5ECF6","aaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"baxis":{"gridcolor":"white","linecolor":"white","ticks":""},"caxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"sequential":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"sequentialminus":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"diverging":[[0,"#8e0152"],[0.1,"#c51b7d"],[0.2,"#de77ae"],[0.3,"#f1b6da"],[0.4,"#fde0ef"],[0.5,"#f7f7f7"],[0.6,"#e6f5d0"],[0.7,"#b8e186"],[0.8,"#7fbc41"],[0.9,"#4d9221"],[1,"#276419"]]},"xaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"yaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"scene":{"xaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"yaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"zaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2}},"shapedefaults":{"line":{"color":"#2a3f5f"}},"annotationdefaults":{"arrowcolor":"#2a3f5f","arrowhead":0,"arrowwidth":1},"geo":{"bgcolor":"white","landcolor":"#E5ECF6","subunitcolor":"white","showland":true,"showlakes":true,"lakecolor":"white"},"title":{"x":0.05},"mapbox":{"style":"light"}}},"xaxis":{"anchor":"y","domain":[0.0,1.0],"title":{"text":"all-mpnet-base-v2"}},"yaxis":{"anchor":"x","domain":[0.0,1.0],"title":{"text":"paraphrase-multilingual-mpnet-base-v2"}},"title":{"text":"Comparison of all-mpnet-base-v2 vs paraphrase-multilingual-mpnet-base-v2"}},                        {"responsive": true}                    ).then(function(){

var gd = document.getElementById('aa5ecdc5-2d06-436d-b634-29e03cd15174');
var x = new MutationObserver(function (mutations, observer) {{
        var display = window.getComputedStyle(gd).display;
        if (!display || display === 'none') {{
            console.log([gd, 'removed!']);
            Plotly.purge(gd);
            observer.disconnect();
        }}
}});

// Listen for the removal of the full notebook cells
var notebookContainer = gd.closest('#notebook-container');
if (notebookContainer) {{
    x.observe(notebookContainer, {childList: true});
}}

// Listen for the clearing of the current output cell
var outputEl = gd.closest('.output');
if (outputEl) {{
    x.observe(outputEl, {childList: true});
}}

                        })                };                });            </script>        </div>



<div>                            <div id="d95308c0-146b-49da-b325-b06dfa83e3e4" class="plotly-graph-div" style="height:525px; width:100%;"></div>            <script type="text/javascript">                require(["plotly"], function(Plotly) {                    window.PLOTLYENV=window.PLOTLYENV || {};                                    if (document.getElementById("d95308c0-146b-49da-b325-b06dfa83e3e4")) {                    Plotly.newPlot(                        "d95308c0-146b-49da-b325-b06dfa83e3e4",                        [{"marker":{"opacity":0.5},"mode":"markers","name":"He said th","x":[894,874,870],"y":[894,870,874],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` Usually","x":[596,592,601],"y":[596,592,594],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Robinson t","x":[942,943,939],"y":[942,943,944],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` I'm a m","x":[1593,1592,1913],"y":[1593,1592,599],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Each had b","x":[827,786,1747],"y":[827,826,833],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mrs. Arthu","x":[699,727,631],"y":[699,727,579],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Dr. Clark ","x":[1171,1167,1170],"y":[1171,1167,1169],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Aj .","x":[1034,836,632],"y":[1034,836,656],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Gauer work","x":[212,276,282],"y":[212,1858,1364],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The three ","x":[1628,1618,1630],"y":[1628,1618,1621],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Last week ","x":[1867,1868,1845],"y":[1867,1865,1868],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Backs high","x":[1776,1764,1763],"y":[1776,1763,1777],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` Our int","x":[85,86,88],"y":[85,86,84],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Managing D","x":[1733,1537,1529],"y":[1733,1737,1753],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Legislator","x":[1266,1223,1269],"y":[1266,1223,1221],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Miss Burke","x":[486,474,480],"y":[486,476,482],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The only d","x":[1393,1392,1396],"y":[1393,1396,1392],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The Mayor ","x":[1547,316,1545],"y":[1547,1030,1690],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"A capsule ","x":[1910,1907,1912],"y":[1910,1907,1912],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"They have ","x":[1028,446,655],"y":[1028,446,1638],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Regrets at","x":[1452,1465,1441],"y":[1452,1465,1441],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"A couple o","x":[270,311,266],"y":[270,267,9],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Three were","x":[1931,1973,1936],"y":[1931,1973,53],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"From the o","x":[846,845,1271],"y":[846,845,1294],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He will be","x":[1050,209,1039],"y":[1050,209,1039],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Wexler had","x":[1216,1208,1209],"y":[1216,1203,1212],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Chester O.","x":[1175,741,828],"y":[1175,893,741],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mrs. Henry","x":[454,668,579],"y":[454,579,697],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"I never di","x":[20,19,53],"y":[20,19,53],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"On Friday ","x":[1862,1828,1863],"y":[1862,1831,841],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Georgia Re","x":[1040,1046,1044],"y":[1040,1070,1052],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` He knoc","x":[49,120,387],"y":[49,1495,51],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"So he woun","x":[285,297,286],"y":[285,296,1261],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He's been ","x":[503,809,502],"y":[503,64,502],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The change","x":[1883,1884,1882],"y":[1883,1884,1882],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Concern ba","x":[1735,1736,1512],"y":[1735,1736,1740],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mrs. Roger","x":[578,744,645],"y":[578,699,661],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"While deta","x":[1117,1116,1418],"y":[1117,1116,1151],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He assured","x":[1421,1385,1855],"y":[1421,1213,1383],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"In another","x":[603,605,602],"y":[603,602,605],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Barber , w","x":[1072,1074,1071],"y":[1072,1074,1067],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Only Bucky","x":[206,205,177],"y":[206,205,178],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"know enoug","x":[1755,1749,1752],"y":[1755,1749,1741],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"After a le","x":[347,346,349],"y":[347,346,127],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"His sense ","x":[1352,1346,1350],"y":[1352,1348,1346],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"It made hi","x":[271,275,324],"y":[271,298,156],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"It was gre","x":[1442,1857,1275],"y":[1442,1648,1454],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Services t","x":[988,987,998],"y":[988,987,991],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"As we bull","x":[505,436,629],"y":[505,146,1638],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The contra","x":[1742,1743,1729],"y":[1742,1743,1729],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He said he","x":[158,157,150],"y":[158,157,1449],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Gene Marsh","x":[556,553,340],"y":[556,553,340],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"When the A","x":[761,645,661],"y":[761,661,645],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Some 30 sp","x":[983,984,1217],"y":[983,984,978],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Yes , with","x":[171,1880,580],"y":[171,316,719],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The educat","x":[1576,1580,1139],"y":[1576,1580,1567],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` Lindy M","x":[352,355,362],"y":[352,355,1963],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Kowalski ,","x":[996,824,998],"y":[996,986,995],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"But from a","x":[1643,673,1306],"y":[1643,1330,1686],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"I remember","x":[173,418,133],"y":[173,277,22],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The women ","x":[667,753,721],"y":[667,490,721],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The 22-yea","x":[1970,1172,1953],"y":[1970,1956,1958],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Along with","x":[1363,1374,1354],"y":[1363,1374,1360],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"!","x":[1601,531,470],"y":[1601,81,541],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"She was mo","x":[1989,258,1256],"y":[1989,1256,513],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He succeed","x":[209,1050,1039],"y":[209,1050,224],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Some even ","x":[620,619,610],"y":[620,619,615],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Denials we","x":[1916,1915,1203],"y":[1916,1207,1917],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"They knew ","x":[383,382,917],"y":[383,382,925],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Asked Palm","x":[315,1449,273],"y":[315,316,1476],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"And after ","x":[1335,1334,1024],"y":[1335,1340,1334],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mr. Hawksl","x":[1372,1369,1623],"y":[1372,1369,1355],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Miss Joan ","x":[636,653,637],"y":[636,653,637],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"One advant","x":[1365,1354,1359],"y":[1365,1354,1356],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He was cal","x":[92,277,23],"y":[92,23,277],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Division s","x":[1662,1661,1659],"y":[1662,1661,1658],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The most v","x":[379,380,262],"y":[379,386,387],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"We've been","x":[670,70,69],"y":[670,1280,45],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Rice has n","x":[65,60,73],"y":[65,73,61],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He suggest","x":[1400,1043,1520],"y":[1400,1500,1408],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"There are ","x":[192,1565,1430],"y":[192,608,130],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Nursing ho","x":[1234,1235,1236],"y":[1234,1236,1235],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He also re","x":[1168,1634,1828],"y":[1168,1634,632],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Decisions ","x":[1201,1202,1200],"y":[1201,1202,1200],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Other spea","x":[1872,265,1870],"y":[1872,1869,697],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Ordinary C","x":[1079,1088,1087],"y":[1079,1088,1087],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Just when ","x":[163,412,186],"y":[163,186,419],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"An assista","x":[1564,1388,1351],"y":[1564,930,1388],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"They , on ","x":[925,924,932],"y":[925,1649,383],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The $6,100","x":[1574,1568,1514],"y":[1574,1149,1514],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"But we hav","x":[680,676,684],"y":[680,676,669],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Skorich re","x":[208,220,771],"y":[208,221,220],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Districts ","x":[1677,1679,1721],"y":[1677,1679,1053],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The aged c","x":[1223,1266,1221],"y":[1223,1247,1222],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` We want","x":[1757,1759,1758],"y":[1757,1759,1758],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Now 38 , M","x":[843,845,842],"y":[843,252,1634],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The U. S. ","x":[1590,1591,1575],"y":[1590,1591,1225],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Dick McAul","x":[110,114,111],"y":[110,116,114],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Tactics st","x":[1624,1304,1298],"y":[1624,1301,1287],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Her husban","x":[832,831,794],"y":[832,811,794],"type":"scatter"}],                        {"template":{"data":{"histogram2dcontour":[{"type":"histogram2dcontour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"choropleth":[{"type":"choropleth","colorbar":{"outlinewidth":0,"ticks":""}}],"histogram2d":[{"type":"histogram2d","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmap":[{"type":"heatmap","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmapgl":[{"type":"heatmapgl","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"contourcarpet":[{"type":"contourcarpet","colorbar":{"outlinewidth":0,"ticks":""}}],"contour":[{"type":"contour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"surface":[{"type":"surface","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"mesh3d":[{"type":"mesh3d","colorbar":{"outlinewidth":0,"ticks":""}}],"scatter":[{"fillpattern":{"fillmode":"overlay","size":10,"solidity":0.2},"type":"scatter"}],"parcoords":[{"type":"parcoords","line":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolargl":[{"type":"scatterpolargl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"bar":[{"error_x":{"color":"#2a3f5f"},"error_y":{"color":"#2a3f5f"},"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"scattergeo":[{"type":"scattergeo","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolar":[{"type":"scatterpolar","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"scattergl":[{"type":"scattergl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatter3d":[{"type":"scatter3d","line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattermapbox":[{"type":"scattermapbox","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterternary":[{"type":"scatterternary","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattercarpet":[{"type":"scattercarpet","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"carpet":[{"aaxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"baxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"type":"carpet"}],"table":[{"cells":{"fill":{"color":"#EBF0F8"},"line":{"color":"white"}},"header":{"fill":{"color":"#C8D4E3"},"line":{"color":"white"}},"type":"table"}],"barpolar":[{"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"pie":[{"automargin":true,"type":"pie"}]},"layout":{"autotypenumbers":"strict","colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#2a3f5f"},"hovermode":"closest","hoverlabel":{"align":"left"},"paper_bgcolor":"white","plot_bgcolor":"#E5ECF6","polar":{"bgcolor":"#E5ECF6","angularaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"radialaxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"ternary":{"bgcolor":"#E5ECF6","aaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"baxis":{"gridcolor":"white","linecolor":"white","ticks":""},"caxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"sequential":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"sequentialminus":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"diverging":[[0,"#8e0152"],[0.1,"#c51b7d"],[0.2,"#de77ae"],[0.3,"#f1b6da"],[0.4,"#fde0ef"],[0.5,"#f7f7f7"],[0.6,"#e6f5d0"],[0.7,"#b8e186"],[0.8,"#7fbc41"],[0.9,"#4d9221"],[1,"#276419"]]},"xaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"yaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"scene":{"xaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"yaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"zaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2}},"shapedefaults":{"line":{"color":"#2a3f5f"}},"annotationdefaults":{"arrowcolor":"#2a3f5f","arrowhead":0,"arrowwidth":1},"geo":{"bgcolor":"white","landcolor":"#E5ECF6","subunitcolor":"white","showland":true,"showlakes":true,"lakecolor":"white"},"title":{"x":0.05},"mapbox":{"style":"light"}}},"xaxis":{"anchor":"y","domain":[0.0,1.0],"title":{"text":"all-mpnet-base-v2"}},"yaxis":{"anchor":"x","domain":[0.0,1.0],"title":{"text":"multi-qa-mpnet-base-dot-v1"}},"title":{"text":"Comparison of all-mpnet-base-v2 vs multi-qa-mpnet-base-dot-v1"}},                        {"responsive": true}                    ).then(function(){

var gd = document.getElementById('d95308c0-146b-49da-b325-b06dfa83e3e4');
var x = new MutationObserver(function (mutations, observer) {{
        var display = window.getComputedStyle(gd).display;
        if (!display || display === 'none') {{
            console.log([gd, 'removed!']);
            Plotly.purge(gd);
            observer.disconnect();
        }}
}});

// Listen for the removal of the full notebook cells
var notebookContainer = gd.closest('#notebook-container');
if (notebookContainer) {{
    x.observe(notebookContainer, {childList: true});
}}

// Listen for the clearing of the current output cell
var outputEl = gd.closest('.output');
if (outputEl) {{
    x.observe(outputEl, {childList: true});
}}

                        })                };                });            </script>        </div>



<div>                            <div id="28880cea-9fa7-4507-8614-c1b6fad3440c" class="plotly-graph-div" style="height:525px; width:100%;"></div>            <script type="text/javascript">                require(["plotly"], function(Plotly) {                    window.PLOTLYENV=window.PLOTLYENV || {};                                    if (document.getElementById("28880cea-9fa7-4507-8614-c1b6fad3440c")) {                    Plotly.newPlot(                        "28880cea-9fa7-4507-8614-c1b6fad3440c",                        [{"marker":{"opacity":0.5},"mode":"markers","name":"He said th","x":[894,874,870],"y":[894,870,899],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` Usually","x":[596,592,601],"y":[596,695,592],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Robinson t","x":[942,943,939],"y":[942,944,943],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` I'm a m","x":[1593,1592,1913],"y":[1593,1592,599],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Each had b","x":[827,786,1747],"y":[827,284,53],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mrs. Arthu","x":[699,727,631],"y":[699,726,737],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Dr. Clark ","x":[1171,1167,1170],"y":[1171,1167,1169],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Aj .","x":[1034,836,632],"y":[1034,1663,632],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Gauer work","x":[212,276,282],"y":[212,120,351],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The three ","x":[1628,1618,1630],"y":[1628,1618,1621],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Last week ","x":[1867,1868,1845],"y":[1867,1868,1865],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Backs high","x":[1776,1764,1763],"y":[1776,1764,1778],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` Our int","x":[85,86,88],"y":[85,86,390],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Managing D","x":[1733,1537,1529],"y":[1733,1529,1532],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Legislator","x":[1266,1223,1269],"y":[1266,1223,1221],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Miss Burke","x":[486,474,480],"y":[486,483,480],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The only d","x":[1393,1392,1396],"y":[1393,1392,192],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The Mayor ","x":[1547,316,1545],"y":[1547,1538,1109],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"A capsule ","x":[1910,1907,1912],"y":[1910,1907,1895],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"They have ","x":[1028,446,655],"y":[1028,742,733],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Regrets at","x":[1452,1465,1441],"y":[1452,1469,1512],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"A couple o","x":[270,311,266],"y":[270,311,320],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Three were","x":[1931,1973,1936],"y":[1931,1973,1936],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"From the o","x":[846,845,1271],"y":[846,845,1521],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He will be","x":[1050,209,1039],"y":[1050,209,1826],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Wexler had","x":[1216,1208,1209],"y":[1216,1209,1208],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Chester O.","x":[1175,741,828],"y":[1175,1880,1937],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mrs. Henry","x":[454,668,579],"y":[454,668,580],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"I never di","x":[20,19,53],"y":[20,19,43],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"On Friday ","x":[1862,1828,1863],"y":[1862,1828,1863],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Georgia Re","x":[1040,1046,1044],"y":[1040,1501,1439],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` He knoc","x":[49,120,387],"y":[49,55,63],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"So he woun","x":[285,297,286],"y":[285,297,294],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He's been ","x":[503,809,502],"y":[503,542,502],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The change","x":[1883,1884,1882],"y":[1883,1882,1884],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Concern ba","x":[1735,1736,1512],"y":[1735,1736,1740],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mrs. Roger","x":[578,744,645],"y":[578,731,758],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"While deta","x":[1117,1116,1418],"y":[1117,1485,1069],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He assured","x":[1421,1385,1855],"y":[1421,1414,1908],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"In another","x":[603,605,602],"y":[603,553,610],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Barber , w","x":[1072,1074,1071],"y":[1072,1067,1074],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Only Bucky","x":[206,205,177],"y":[206,177,173],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"know enoug","x":[1755,1749,1752],"y":[1755,1751,1749],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"After a le","x":[347,346,349],"y":[347,346,349],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"His sense ","x":[1352,1346,1350],"y":[1352,1346,1353],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"It made hi","x":[271,275,324],"y":[271,543,426],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"It was gre","x":[1442,1857,1275],"y":[1442,1648,721],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Services t","x":[988,987,998],"y":[988,987,993],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"As we bull","x":[505,436,629],"y":[505,570,485],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The contra","x":[1742,1743,1729],"y":[1742,1743,1729],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He said he","x":[158,157,150],"y":[158,157,1261],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Gene Marsh","x":[556,553,340],"y":[556,553,1907],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"When the A","x":[761,645,661],"y":[761,744,758],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Some 30 sp","x":[983,984,1217],"y":[983,1218,982],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Yes , with","x":[171,1880,580],"y":[171,178,718],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The educat","x":[1576,1580,1139],"y":[1576,1580,1578],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` Lindy M","x":[352,355,362],"y":[352,57,164],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Kowalski ,","x":[996,824,998],"y":[996,994,997],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"But from a","x":[1643,673,1306],"y":[1643,1330,1666],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"I remember","x":[173,418,133],"y":[173,206,418],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The women ","x":[667,753,721],"y":[667,721,702],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The 22-yea","x":[1970,1172,1953],"y":[1970,1958,1976],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Along with","x":[1363,1374,1354],"y":[1363,1360,1374],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"!","x":[1601,531,470],"y":[535,1601,531],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"She was mo","x":[1989,258,1256],"y":[1989,1774,692],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He succeed","x":[209,1050,1039],"y":[209,226,1050],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Some even ","x":[620,619,610],"y":[620,619,1875],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Denials we","x":[1916,1915,1203],"y":[1916,976,1196],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"They knew ","x":[383,382,917],"y":[383,1707,1649],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Asked Palm","x":[315,1449,273],"y":[315,297,307],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"And after ","x":[1335,1334,1024],"y":[1335,1334,1339],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Mr. Hawksl","x":[1372,1369,1623],"y":[1372,1364,1369],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Miss Joan ","x":[636,653,637],"y":[636,653,645],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"One advant","x":[1365,1354,1359],"y":[1365,1354,1356],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He was cal","x":[92,277,23],"y":[92,277,99],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Division s","x":[1662,1661,1659],"y":[1662,1661,1658],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The most v","x":[379,380,262],"y":[379,386,387],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"We've been","x":[670,70,69],"y":[670,70,819],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Rice has n","x":[65,60,73],"y":[65,61,73],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He suggest","x":[1400,1043,1520],"y":[1400,1541,1088],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"There are ","x":[192,1565,1430],"y":[192,1393,1390],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Nursing ho","x":[1234,1235,1236],"y":[1234,1236,1235],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"He also re","x":[1168,1634,1828],"y":[1168,1167,1828],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Decisions ","x":[1201,1202,1200],"y":[1201,1202,1122],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Other spea","x":[1872,265,1870],"y":[1872,725,1869],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Ordinary C","x":[1079,1088,1087],"y":[1079,1088,1087],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Just when ","x":[163,412,186],"y":[163,186,432],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"An assista","x":[1564,1388,1351],"y":[1564,1825,1350],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"They , on ","x":[925,924,932],"y":[925,924,272],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The $6,100","x":[1574,1568,1514],"y":[1574,1568,1124],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"But we hav","x":[680,676,684],"y":[680,676,684],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Skorich re","x":[208,220,771],"y":[208,220,227],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Districts ","x":[1677,1679,1721],"y":[1677,1679,1717],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The aged c","x":[1223,1266,1221],"y":[1223,1266,1222],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"`` We want","x":[1757,1759,1758],"y":[1757,1758,1759],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Now 38 , M","x":[843,845,842],"y":[843,845,842],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"The U. S. ","x":[1590,1591,1575],"y":[1590,1591,1582],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Dick McAul","x":[110,114,111],"y":[110,114,1945],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Tactics st","x":[1624,1304,1298],"y":[1624,1297,1293],"type":"scatter"},{"marker":{"opacity":0.5},"mode":"markers","name":"Her husban","x":[832,831,794],"y":[832,831,971],"type":"scatter"}],                        {"template":{"data":{"histogram2dcontour":[{"type":"histogram2dcontour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"choropleth":[{"type":"choropleth","colorbar":{"outlinewidth":0,"ticks":""}}],"histogram2d":[{"type":"histogram2d","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmap":[{"type":"heatmap","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"heatmapgl":[{"type":"heatmapgl","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"contourcarpet":[{"type":"contourcarpet","colorbar":{"outlinewidth":0,"ticks":""}}],"contour":[{"type":"contour","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"surface":[{"type":"surface","colorbar":{"outlinewidth":0,"ticks":""},"colorscale":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]]}],"mesh3d":[{"type":"mesh3d","colorbar":{"outlinewidth":0,"ticks":""}}],"scatter":[{"fillpattern":{"fillmode":"overlay","size":10,"solidity":0.2},"type":"scatter"}],"parcoords":[{"type":"parcoords","line":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolargl":[{"type":"scatterpolargl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"bar":[{"error_x":{"color":"#2a3f5f"},"error_y":{"color":"#2a3f5f"},"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"bar"}],"scattergeo":[{"type":"scattergeo","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterpolar":[{"type":"scatterpolar","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"histogram":[{"marker":{"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"histogram"}],"scattergl":[{"type":"scattergl","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatter3d":[{"type":"scatter3d","line":{"colorbar":{"outlinewidth":0,"ticks":""}},"marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattermapbox":[{"type":"scattermapbox","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scatterternary":[{"type":"scatterternary","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"scattercarpet":[{"type":"scattercarpet","marker":{"colorbar":{"outlinewidth":0,"ticks":""}}}],"carpet":[{"aaxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"baxis":{"endlinecolor":"#2a3f5f","gridcolor":"white","linecolor":"white","minorgridcolor":"white","startlinecolor":"#2a3f5f"},"type":"carpet"}],"table":[{"cells":{"fill":{"color":"#EBF0F8"},"line":{"color":"white"}},"header":{"fill":{"color":"#C8D4E3"},"line":{"color":"white"}},"type":"table"}],"barpolar":[{"marker":{"line":{"color":"#E5ECF6","width":0.5},"pattern":{"fillmode":"overlay","size":10,"solidity":0.2}},"type":"barpolar"}],"pie":[{"automargin":true,"type":"pie"}]},"layout":{"autotypenumbers":"strict","colorway":["#636efa","#EF553B","#00cc96","#ab63fa","#FFA15A","#19d3f3","#FF6692","#B6E880","#FF97FF","#FECB52"],"font":{"color":"#2a3f5f"},"hovermode":"closest","hoverlabel":{"align":"left"},"paper_bgcolor":"white","plot_bgcolor":"#E5ECF6","polar":{"bgcolor":"#E5ECF6","angularaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"radialaxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"ternary":{"bgcolor":"#E5ECF6","aaxis":{"gridcolor":"white","linecolor":"white","ticks":""},"baxis":{"gridcolor":"white","linecolor":"white","ticks":""},"caxis":{"gridcolor":"white","linecolor":"white","ticks":""}},"coloraxis":{"colorbar":{"outlinewidth":0,"ticks":""}},"colorscale":{"sequential":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"sequentialminus":[[0.0,"#0d0887"],[0.1111111111111111,"#46039f"],[0.2222222222222222,"#7201a8"],[0.3333333333333333,"#9c179e"],[0.4444444444444444,"#bd3786"],[0.5555555555555556,"#d8576b"],[0.6666666666666666,"#ed7953"],[0.7777777777777778,"#fb9f3a"],[0.8888888888888888,"#fdca26"],[1.0,"#f0f921"]],"diverging":[[0,"#8e0152"],[0.1,"#c51b7d"],[0.2,"#de77ae"],[0.3,"#f1b6da"],[0.4,"#fde0ef"],[0.5,"#f7f7f7"],[0.6,"#e6f5d0"],[0.7,"#b8e186"],[0.8,"#7fbc41"],[0.9,"#4d9221"],[1,"#276419"]]},"xaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"yaxis":{"gridcolor":"white","linecolor":"white","ticks":"","title":{"standoff":15},"zerolinecolor":"white","automargin":true,"zerolinewidth":2},"scene":{"xaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"yaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2},"zaxis":{"backgroundcolor":"#E5ECF6","gridcolor":"white","linecolor":"white","showbackground":true,"ticks":"","zerolinecolor":"white","gridwidth":2}},"shapedefaults":{"line":{"color":"#2a3f5f"}},"annotationdefaults":{"arrowcolor":"#2a3f5f","arrowhead":0,"arrowwidth":1},"geo":{"bgcolor":"white","landcolor":"#E5ECF6","subunitcolor":"white","showland":true,"showlakes":true,"lakecolor":"white"},"title":{"x":0.05},"mapbox":{"style":"light"}}},"xaxis":{"anchor":"y","domain":[0.0,1.0],"title":{"text":"all-mpnet-base-v2"}},"yaxis":{"anchor":"x","domain":[0.0,1.0],"title":{"text":"all-MiniLM-L6-v2"}},"title":{"text":"Comparison of all-mpnet-base-v2 vs all-MiniLM-L6-v2"}},                        {"responsive": true}                    ).then(function(){

var gd = document.getElementById('28880cea-9fa7-4507-8614-c1b6fad3440c');
var x = new MutationObserver(function (mutations, observer) {{
        var display = window.getComputedStyle(gd).display;
        if (!display || display === 'none') {{
            console.log([gd, 'removed!']);
            Plotly.purge(gd);
            observer.disconnect();
        }}
}});

// Listen for the removal of the full notebook cells
var notebookContainer = gd.closest('#notebook-container');
if (notebookContainer) {{
    x.observe(notebookContainer, {childList: true});
}}

// Listen for the clearing of the current output cell
var outputEl = gd.closest('.output');
if (outputEl) {{
    x.observe(outputEl, {childList: true});
}}

                        })                };                });            </script>        </div>
