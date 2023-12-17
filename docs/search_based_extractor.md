# Search Based Extractor

Utility to simplify webscraping by taking advantave of search and assumptions about html structure.
Extractor allows to find parent html element that contains searched term, record path to it in a file
and reuse that to scrape data with same html structure.


```python
import sys
sys.path.append('../')
from python_modules.search_based_extractor import SearchBasedExtractor
```

## Usage examples

The examples contain: 
1. recording path the parent \<div> element on the page [review_id=7207](https://metalstorm.net/pub/review.php?review_id=7207) based on some text from that element;
2. using recorded path to scrape content of the [review_id=16350](https://metalstorm.net/pub/review.php?review_id=16350).

### 1 Recording path

#### 1.1. Initialize extractor object 


```python
sbe = SearchBasedExtractor(
    # optionally 
    ## provide filename to persist state
    filename = 'recorded_sbe.json',
    ## provide soup for scraping if was already defined externally
    soup = None
)
```

#### 1.2. Point to the part of a page where scraping should be done


```python
# provide link to the page and initialize internal soup
sbe.initialize_soup(link = 'https://metalstorm.net/pub/review.php?review_id=7207')
# create path element to the parent <div> of the searched text
sbe.find_path_with_text(search_text = "I'm not a huge fan of nu-metal right now")
```

#### 1.3. Make sure that detected path points to the desired content


```python
# first 500 lines of visible text on a given page
sbe.extract_visible_text(new_line_separator = '\n')[0:500]
```




    'html\n Korn - See You On The Other Side review - Metal Storm\n Login\n Register\n Toggle navigation\n band\n style\n album\n video\n musician\n event\n forum\n user\n Metal Storm\n Metal Storm\n Home\n About us\n Metal Storm Awards\n Site tour\n FAQ\n Promo media\n Community\n Community\n Forum\n Members\n Top lists\n Tradelist\n Staff\n Bands\n Bands\n Bands\n Albums\n Album charts\n Top 200 albums\n Videos\n Musicians\n News & events\n News & events\n Combined updates\n News\n New releases\n Upcoming releases\n Events\n Metal locations'




```python
# extracted content based on searched text
print(sbe.extract_from_path())
```

    
    
    Reviewer:
    8.3370 users:
    6.02
    
    
    
    
    Band:
    
    Korn
    
    
    
    Album:
    
    
    See You On The Other Side
    
    
    
    Release date:
    
     December 2005
    
    Disc I01. Twisted Transistor02. Politics03. Hypocrites04. Souvenir05. 10 Or A 2-Way06. Throw Me Away07. Love Song08. Open Up09. Coming Undone10. Getting Off11. Liar12. For No One13. Seen It All14. Tearjerker15. Too Late I'm Dead [Japanese deluxe edition bonus]Disc II Deluxe Edition & Japanese Deluxe Edition01. It's Me Again02. Eaten Up Inside03. Last Legal Drug (Le Petit Mort)04. Twisted Transistor [The Dante Ross Mix]05. Twisted Transistor [Dummies Club Mix]+  Twisted Transistor [video] [Live In Moscow]+  Hypocrites [video] [Live In Moscow]+  One Year Membership To KoRn BSC Fan Club featuring exclusive behind-the-scenes media content, Korn community membership with personal home page and blog, pre-sale ticket access for the Korn tour [deluxe edition bonus]+  Password access to two digital download tracks at Best Buy Exclusive! [deluxe edition bonus]+  One Year Membership To KoRn BSC Fan Club with two books, first with texts of songs in English and Japanese, and second with pictures [japanese deluxe edition bonus]I'm not a huge fan of nu-metal right now, but Korn used to be a favourite of mine. They've been trying to re-invent themselves for a while now, from the electronic beats and strings on Untouchables to the hard-hitting Take A Look In The Mirror, to the borderline-electronica of the untitled album. But I still think that this album, where Korn went industrial, was their most successful attempt at reinvention yet, and made the untitled album even more disappointing. 
    
    Firstly, Korn brought on two big-name producers - Atticus Ross, of the band 12 Rounds, and at that point working with Nine Inch Nails; and the Matrix, a group whose clients have included Hilary Duff and Avril Lavigne. Jonathan Davis also steps behind the boards, as he's done for every Korn album since Follow The Leader (bar Issues). While hardcore Korn devotees gnash their teeth at having their heroes in proximity to Hilary Duff's schlockmeisters, it worked. Take lead single "Twisted Transistor", for example. It's laden with pop hooks, Munky's simple riff takes center stage, and Jonathan Davis isn't singing with rage, but rather with a kind of morbid happiness. Amazingly, this is one of the best songs they've written in a while, grinding away with thick industrial rhythms and morbid imagery of sex and violence ("hold it between your legs, turn it up, turn it up"; the distorted growl of "This won't hurt a bit" near the end). This is Korn, and pop for them is anything but fun. 
    
    "Twisted Transistor" and the other two singles, "Coming Undone" and "Politics", take center stage on this album. "Coming Undone" is another one of their better songs, stripped-down, crunchy and stomping away, reminiscent of Take A Look In The Mirror. "Politics" is another pointed stomp, but there's some wonderful synth ambience courtesy of Atticus Ross, and Davis' rant about not caring about politics is really quite useful for this day and age. Three of Korn's better singles, to be sure, but there's some other gems buried in the mix. Davis' contorted vocals sound, not filled with rage and vengeance as they did on Follow Your Leader, but more three-dimensional, able to express more emotion. And with Head's departure, the three remaining members besides Davis sound downright vengeful, Munky's sizzling seven-string attack, Fieldy's slinky, funky basslines and David Silveria's pounding rhythms beating the songs into your head. 
    
    The album tracks are just as good. Sure, there are some failed experiments - they try a bit too hard to be Nine Inch Nails on "Throw Me Away", "Seen It All" doesn't blend its influence successfully, and the bonus track "Eaten Up Inside" is just that bit too slick - but hey, there's some great ones too. The Nine Inch Nails influence works on the synth-rock rhythms of "Open Up", and the heavy metallic grind of "Liar" and "Getting Off" remind me somewhat of Follow The Leader. 
    
    Overall See You On The Other Side is a good album, with a few mediocre tracks. But hey, Korn have reinvented themselves, and very nicely at that. Actually, on further reflection, it might be their best album. Their follow-up, on the other hand, is their worst...but that's for another time.
    Written by [insert name] | 09.10.2009
     
    
    Tweet
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    Guest review disclaimer:
    This is a guest review, which means it does not necessarily represent the point of view of the MS Staff.
    



```python
# extracted content based on searched text, given optional start and end of the content
print(sbe.extract_from_path(search_text_start="I'm not a huge fan of nu-metal right now",
                            search_text_end="Written by"))
```

    I'm not a huge fan of nu-metal right now, but Korn used to be a favourite of mine. They've been trying to re-invent themselves for a while now, from the electronic beats and strings on Untouchables to the hard-hitting Take A Look In The Mirror, to the borderline-electronica of the untitled album. But I still think that this album, where Korn went industrial, was their most successful attempt at reinvention yet, and made the untitled album even more disappointing. 
    
    Firstly, Korn brought on two big-name producers - Atticus Ross, of the band 12 Rounds, and at that point working with Nine Inch Nails; and the Matrix, a group whose clients have included Hilary Duff and Avril Lavigne. Jonathan Davis also steps behind the boards, as he's done for every Korn album since Follow The Leader (bar Issues). While hardcore Korn devotees gnash their teeth at having their heroes in proximity to Hilary Duff's schlockmeisters, it worked. Take lead single "Twisted Transistor", for example. It's laden with pop hooks, Munky's simple riff takes center stage, and Jonathan Davis isn't singing with rage, but rather with a kind of morbid happiness. Amazingly, this is one of the best songs they've written in a while, grinding away with thick industrial rhythms and morbid imagery of sex and violence ("hold it between your legs, turn it up, turn it up"; the distorted growl of "This won't hurt a bit" near the end). This is Korn, and pop for them is anything but fun. 
    
    "Twisted Transistor" and the other two singles, "Coming Undone" and "Politics", take center stage on this album. "Coming Undone" is another one of their better songs, stripped-down, crunchy and stomping away, reminiscent of Take A Look In The Mirror. "Politics" is another pointed stomp, but there's some wonderful synth ambience courtesy of Atticus Ross, and Davis' rant about not caring about politics is really quite useful for this day and age. Three of Korn's better singles, to be sure, but there's some other gems buried in the mix. Davis' contorted vocals sound, not filled with rage and vengeance as they did on Follow Your Leader, but more three-dimensional, able to express more emotion. And with Head's departure, the three remaining members besides Davis sound downright vengeful, Munky's sizzling seven-string attack, Fieldy's slinky, funky basslines and David Silveria's pounding rhythms beating the songs into your head. 
    
    The album tracks are just as good. Sure, there are some failed experiments - they try a bit too hard to be Nine Inch Nails on "Throw Me Away", "Seen It All" doesn't blend its influence successfully, and the bonus track "Eaten Up Inside" is just that bit too slick - but hey, there's some great ones too. The Nine Inch Nails influence works on the synth-rock rhythms of "Open Up", and the heavy metallic grind of "Liar" and "Getting Off" remind me somewhat of Follow The Leader. 
    
    Overall See You On The Other Side is a good album, with a few mediocre tracks. But hey, Korn have reinvented themselves, and very nicely at that. Actually, on further reflection, it might be their best album. Their follow-up, on the other hand, is their worst...but that's for another time.
    


#### 1.4. Save path to a json file


```python
sbe.save_recorded_sbe()
```

    INFO:SearchBasedExtractor:Data saved to 'recorded_sbe.json'



```python
# inspected saved path 
sbe.show_recorded_sbe()
```

    Link: https://metalstorm.net/pub/review.php?review_id=7207
    Searched Text: I'm not a huge fan of nu-metal right now
    Path: [['[document]', 0], ['html', 0], ['body', 0], ['div', 1], ['div', 1], ['div', 0], ['div', 0], ['div', 2], ['div', 0], ['div', 0], ['div', 1]]


### 2. Use recorded path to scrape new data

#### 2.1 Initialize new extractor object


```python
sbe = SearchBasedExtractor()
# load recorded path file
sbe.load_recorded_sbe()
```

    INFO:SearchBasedExtractor:Path loaded from recorded_sbe.json


#### 2.2 Define soup based on new link


```python
sbe.initialize_soup(link = 'https://metalstorm.net/pub/review.php?review_id=16350')
```

#### 2.3 Extract new content based on recorded path


```python
print(sbe.extract_from_path())
```

    
    
    Reviewer:
    7.8323 users:
    8.25
    
    
    
    
    Band:
    
    Mors Principium Est
    
    
    
    Album:
    
    
    Seven
    
    
    
    Release date:
    
     October 2020
    
    01. A Day For Redemption02. Lost In A Starless Aeon03. In Frozen Fields04. March To War05. Rebirth06. Reverence07. Master Of The Dead08. The Everlong Night09. At The Shores Of Silver Sand10. My Home, My GraveMors Principium Est are one of the most reliable bands in melodeath, and Seven has no plans of changing that reputation. 
    
    In contrast to their compatriots in Insomnium and Omnium Gatherum, Mors Principium Est veer away from the melancholic melodeath sound associated with Finland and instead take a somewhat more Gothenburg-rooted approach, albeit with increased technicality and a more symphonic approach from the keyboards compared with the likes of Dark Tranquillity; there's certainly a hint of the extreme power sound of Kalmah or Children Of Bodom somewhere in there (although the Dark Tranquillity is strong on "The Everlong Night" here). Whilst they've not quite developed the followings that the biggest Gothenburg or Finnish melodeath groups have accumulated, each new record has been hotly anticipated and well-received, meaning that the group enter their seventh record, helpfully titled Seven, with a lot of momentum behind them.
    
    The formula here is very much the same as on the previous couple of records, although the dalliances with more Gothic territory that popped up on previous record Embers Of A Dying World have not been carried over onto Seven. The album is for the most part (the interlude "Reverence" being the only notable exception) one up-tempo melodeath celebration of riffs and hooky guitar licks after another; the band elect not to begin with a standalone short introductory symphonic track this time around, instead packaging said dramatic intro into "A Day For Redemption" alongside the very classic-sounding melodeath song that follows. The emphatic, ear-catching guitar leads, energetic and technically minded riffs and symphonic interjections; everything you would expect from the opening track of a Mors Principium Est is here and ready to feed hungry fans. "Lost In A Starless Aeon" carries on much the same, the verses peppered with exciting harmonized guitar arpeggios and the chorus instantly memorable.
    
    "Lost In A Starless Aeon" is an early highlight, but it's not the only quality track here. Most of my other top picks lurk towards the end of the album. "Master Of The Dead" has some solid riffs and effective use of synths, as well as probably the most memorable solo on the record, although the sweeps on "At The Shores Of Silver Sand" may rival it for that title. Probably the most consistently attention-grabbing song for me, however, was closer "My Home, My Grave"; the chorus on this song is the only one outside of that in "Lost In A Starless Aeon" that stuck with me each time the album, a perfect combination Finnish melodeath guitar leads, suspenseful chords and ripping vocals. It was the one track that I've found myself getting excited over as soon as it started each time I've run through Seven, and it makes for a pretty epic conclusion to the record.
    
    So, Seven offers more of the classic Mors Principium Est sound, and does it well. However, I'm not sure it's the best rendition of it; having revisited their previous two records in between replays of this, I find the tracks on Dawn Of The 5th Era and Embers Of A Dying World more consistently memorable than those on Seven. I feel like including some of the diversity that those Gothic tangents on their last record offered would have helped with that, as without something like that, a lot of tracks here do blend together, despite little flourishes such as the big symphonic opening to "March To War" that offer brief changes in pace; each song in isolation sounds good and enjoyable, but together in a row, it feels like hearing the same guitar leads and riffs slightly reworked on a song-to-song basis, particularly due to the frantic, technical nature of the riffs.
    
    I can see this being considered slightly nitpicky; plenty of bands in melodeath and death metal fill their records with songs all in the same style, and if it's a band with as strong a sound as Mors Principium Est putting out a bunch of new songs all in their signature style, it's hard to see big fans of the group complaining. However, as someone with a passing rather than vested interest in Mors Principium Est, the combination of the lack of variety and the lack of especially memorable hooks (fast melodic riffs such as those found in abundance here sound very cool, but it's hard to remember one when you're barraged with dozens that sound very similar) does mean that on the times that I wish to revisit the group, Seven isn't likely to be the album I feel most strongly inclined to put on. Nevertheless, for those that just want to hear Mors Principium Est be Mors Principium Est, I would be surprised if Seven does not scratch that itch in a highly satisfying manner.
    
    Rating breakdown
    
    
    Performance:
    
    9
    
    
    Songwriting:
    
    7
    
    
    Originality:
    
    6
    
    
    Production:
    
    9
    
     
    
    Tweet
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    Written on 25.10.2020 by
    musclassia
    						Hey chief let's talk why not
    						
    					
    
    
    
    More reviews by musclassia ››
    
    

