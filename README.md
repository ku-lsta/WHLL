# WHLL: Wikipedia Hyperlink-based Location Linking

WHLL (Wikipedia Hyperlink-based Location Linking) is a method for automatic construction of corpora annotated with coordinates (latitudes and longitudes) from Wikipedia dumps.

## Requirements

- BeautifulSoup4
- tqdm

## Usage

1. Download Wikipedia dumps from https://dumps.wikimedia.org/ .
   - CirrusSearch dump
	 - for coordinates dictionary of articles
	 - Other files > CirrusSearch - Search indexes dumped in elasticsearch bulk insert format
	 - {language_code}wiki-{date}-cirrussearch-content.json.gz (e.g. jawiki-20240304-cirrussearch-content.json.gz)
   - Enterprise HTML dump
	 - for html texts of articles
	 - Other files > HTML dumps of articles from select wiki projects in gzip compressed json format (mirrored from Wikimedia Enterprise)
	 - {language_code}wiki-NS0-{date}-ENTERPRISE-HTML.json.tar.gz (e.g. jawiki-NS0-20240301-ENTERPRISE-HTML.json.tar.gz)
	 - Extract the file after downloading.
	 
2. Run WHLL.py
   - ```python WHLL.py /path/to/cirrussearch_dump /path/to/html_dump_dir /path/to/output_dir --make_coord```
   
3. Check output files
   - coord.tsv
> Title	Latitude	Longitude	ArticleID	is_redirect<br>
> Mid Antrim (Northern Ireland Parliament constituency)   54.91100        -6.14700        10000032        0<br>
> Antrim Mid (Northern Ireland Parliament constituency)   54.91100        -6.14700        10000032        1<br>
   - {fileid}.jsonl
	 - JSON Lines format
		 - id: article id
		 - title: article title
		 - text: article body text
		 - gold: list of location expressions
			 - [start\_pos, end\_pos, expression, [latitude, longitude]]
> {<br>
>	"id": 187911,<br>
>	"title": "Kyoto University",<br>
>	"text": " (京都大学, Kyōto daigaku), or  (京大, Kyōdai), is a public research university located in Kyoto, Japan. Founded in 1897, ...",<br>
>	"gold": [[85, 90, "Kyoto", [35.01167, 135.76833]], [92, 97, "Japan", [36.0, 138.0]], ...]<br>
> }
   
## Citing WHLL (TBA)

```
@inproceedings{ohno2024automatic,
	title={Automatic Construction of a Large-Scale Corpus for Geoparsing Using Wikipedia Hyperlinks},
	author={Ohno, Keyaki and Kameko, Hirotaka and Shirai, Keisuke and Nishimura, Taichi and Mori, Shinsuke},
	booktitle={Proceedings of The 2024 Joint International Conference on Computational Linguistics, Language Resources and Evaluation (LREC-COLING 2024)},
	year=2024,
}
```
