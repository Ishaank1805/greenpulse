# Mid-sem presentation: who presents what, and what to say

Deck: `greenpulse-mideval.pptx` (21 slides). Each script is written to be read aloud at a normal pace, about 45–70 seconds per slide, roughly **17 minutes** in total. If the TA gives a shorter slot, trim the lines marked *(optional)* first.

"If asked" lines are not part of the talk. They are ready answers for questions.

## Who presents which slides

| Presenter | Slides | Part |
| --- | --- | --- |
| **Role 4** (Prajna) | 1, 2, 3, 4, 17, 20 | Opening, problem statement, exposure result, observations |
| **Role 1** (Himani) | 5, 6, 8, 9 | Data, study area, how a city becomes a grid |
| **Role 5** | 7, 18, 21 | Why no monsoon, the water check, limitations and next steps |
| **Role 3** | 10, 12, 16, 19 | The cooling slope, pilot, seasons, robustness |
| **Role 2** | 11, 13, 14, 15 | Climate method, the rainfall result, the map, dry cities vs Guo |

**Running order of speakers:**

| Slides | Presenter |
| --- | --- |
| 1–4 | R4 |
| 5–6 | R1 |
| 7 | R5 |
| 8–9 | R1 |
| 10 | R3 |
| 11 | R2 |
| 12 | R3 |
| 13–15 | R2 |
| 16 | R3 |
| 17 | R4 |
| 18 | R5 |
| 19 | R3 |
| 20 | R4 |
| 21 | R5 |

Each script ends with a one-line handover, so changes of speaker sound smooth.

**Two changes from the earlier plan:**
- **Slide 11:** Role 2 presents all of it, people-weighting included, so the slide isn't split between two speakers. Role 4 re-explains people-weighting in one sentence on slide 17.
- **Slide 21:** Role 5 presents it, because limitations are mostly data limits. This also balances the slide count.

---

## Slide 1: Title (Role 4)

> Good morning. We are GreenPulse, and our project is about nature-based solutions for urban heat.
>
> The question is simple to ask: does the greenery that already exists in Indian cities actually cool them, and if so, when does it cool the most?
>
> To answer it, we studied 303 Indian cities using satellite data from 2019 to 2024.

---

## Slide 2: Problem (Role 4)

> Cities are hotter than the land around them. Dense buildings, paved surfaces and waste heat from people all trap heat. Across 419 large cities worldwide, satellites see urban surfaces about 1.5 °C hotter than their surroundings by day, and 1.1 °C at night.
>
> Greening is the usual fix. Trees and parks cool through shade, and through water evaporating from their leaves. Parks are on average about 0.94 °C cooler by day, and trees cool two to three times more than grass or green roofs.
>
> So our research question has two parts. First, does existing urban vegetation measurably reduce heat exposure? And second, under what environmental conditions is that cooling strongest? The second part is where the research disagrees, which is the next slide.

*If asked:* Peng et al. 2012 measured satellite surface temperature, while Bowler et al. 2010 measured air temperature in parks.

---

## Slide 3: The literature disagrees (Role 4)

> The biggest disagreement is about dry climates.
>
> On the left, two large studies say dry cities get **less** cooling. Guo and colleagues looked at 761 cities and found that in 22% of cities with under 1,000 mm of rain a year, vegetation actually causes net warming. Schwaab found that during heat extremes, trees in dry southern Europe cool far less than in central Europe.
>
> On the right, two studies say the opposite. Manoli found greening is *more* efficient in dry regions, but only when it is irrigated. Yang, across 510 cities, found trees cool more efficiently in hot, dry cities.
>
> Three more problems sit at the bottom:
> - A 2026 study of 138 Indian cities found very active canopies go with a higher Heat Index in humid cities.
> - Satellites overstate cooling compared with the air temperature people feel.
> - Most of this evidence comes from Europe, China and North America.
>
> India covers everything from desert to very wet, so it is a natural place to test this.

*If asked "which paper does your method follow?":*
- The cooling slope comes from Yang 2022 and Schwaab 2021.
- Climate as the explanation comes from Zhao 2014, Manoli 2019 and Guo 2026.
- The 1,000 mm threshold comes from Guo and Manoli.
- People-weighting comes from Chakraborty 2019 and Chen 2022.

---

## Slide 4: Hypotheses (Role 4)

> From this, we test five hypotheses.
>
> - **H1:** greener squares are cooler by day in most cities.
> - **H2:** the strength of that cooling changes with how wet or dry the climate is. We let the data tell us which way.
> - **H3:** at night, cooling is weaker, and may even reverse in dry cities.
> - **H4:** the same city cools differently before and after the monsoon.
> - **H5:** crowded areas are less green and hotter, so people feel more heat than the city average suggests.
>
> A sixth hypothesis, about the heat people actually feel, is our next piece of work after the mid-sem.
>
> Each of these has a results slide later. I'll now hand over to Himani for the data.

---

## Slide 5: Data (Role 1)

> We used seven free, open datasets. Six come from Google Earth Engine, plus OpenStreetMap.
>
> - **Surface temperature:** the MODIS satellite, at 1 km, every 8 days, at about 1:30 in the afternoon and 1:30 at night. We chose the Aqua satellite because its afternoon pass is close to the hottest part of the day.
> - **Greenness:** NDVI from MODIS, with EVI as a check.
> - **City climate:** ERA5-Land, which gives rainfall, temperature, humidity and soil moisture.
> - **Built-up land** from GHSL, **population** from WorldPop, **water** from OpenStreetMap, and **elevation** from SRTM.
>
> Five of these were assigned. We added elevation as a control, and use OpenStreetMap only for water.

*If asked why 1 km when other layers are 100 m:* 1 km is the native resolution of the temperature data. We average the finer layers up to 1 km, never the other way, because shrinking temperature to 100 m would invent detail the satellite never measured.

*If asked:* LST is the temperature of surfaces such as roofs, roads and leaves, not of the air people breathe.

---

## Slide 6: Study area (Role 1)

> Our cities are every urban centre in India with more than 3 lakh people. That gives 303 cities. A city here is defined by the same rule everywhere: connected 1 km cells that are densely built and populated. So we are not relying on municipal boundaries, which differ from state to state.
>
> The cities cover the full range of rainfall: from 262 mm a year in Bikaner to nearly 3,800 mm in Darjeeling. Jodhpur, one of our pilot cities, gets about 400 mm, and Kochi gets over 3,000.
>
> We look at three seasons, each averaged over six years:
> - pre-monsoon, in April and May
> - post-monsoon, in October and November
> - winter
>
> The seasons really do differ. The typical square is almost 40 °C by day before the monsoon, but about 28 °C in winter.
>
> *(optional)* In total that is about 53,000 squares and nearly 300 million people.

*If asked why Kochi is warmer in winter than before the monsoon:* Kerala is already wet in April and May, with over 600 mm of rain in Kochi, while its winter is dry and sunny.

*Handover:* "Next, our teammate will explain why there is no monsoon season."

---

## Slide 7: Why no monsoon (Role 5)

> You might ask why we leave out the monsoon, which is when Indian cities change the most. The answer is cloud.
>
> Satellites cannot measure surface temperature through cloud. We used the same quality filter as our main analysis and counted the usable images month by month in six cities. In Mumbai, about 85% of daytime images are usable in April and May. In June to September, that drops to about 25%. Kolkata falls to 19%.
>
> The loss is also uneven between cities, so monsoon results would rest on very different amounts of data in each city. An earlier India-wide study, Kumar and colleagues in 2017, left out the monsoon for the same reason.

*If asked why these numbers are lower than the ~98% mentioned elsewhere:* this chart counts every square in the city outline, including water, which never gives a land reading. Compare the months within this chart.

*Handover:* "Back to Himani for how each city becomes data."

---

## Slide 8: Each city becomes a grid (Role 1)

> Here is how each city becomes data, in four steps.
>
> 1. We lay the 1 km satellite grid over the city outline.
> 2. We keep only reliable readings. Cloudy readings are thrown out. A square with no reading at all, in any season, is open water.
> 3. For each square we average six years of data in each season: day and night temperature, greenness, built-up share, population and elevation.
> 4. We keep only urban squares, meaning at least 10% built-up, because our question is about urban vegetation.
>
> A city needs at least 30 urban squares for a reliable estimate, and 202 of our 303 cities have that.
>
> We checked the pipeline carefully:
> - It reproduces our pilot numbers exactly.
> - Its population totals match WorldPop within 0.02%.
> - Every value in every city passed range checks.

*If asked how you know missing squares are water and not cloud:* a cloudy square would be missing in some seasons only. In every city, exactly the same squares are missing in all three seasons.

*If asked about the 101 dropped cities:* they have fewer than 30 urban squares, a median of 19. They are smaller cities, and they are still in our data; they just don't give a reliable slope.

---

## Slide 9: Jodhpur example (Role 1)

> This is what the analysis actually sees, using Jodhpur before the monsoon. Each coloured block is one of its 254 squares. On the left is daytime surface temperature, and on the right is greenness.
>
> The hottest squares, in dark red, are along the bare south-western edge of the city, and they are not green. But notice that some pale, less green squares in the north are also cool. So by eye, the link between green and cool is not clean.
>
> That is because the city's bare desert outskirts are hotter than its built-up core, which hides the effect of greenery. The next slide shows how we separate the two.

*Handover:* "Over to our teammate for how we measure cooling."

---

## Slide 10: The cooling slope (Role 3)

> Our key number is the cooling slope. For each city, we fit this regression across its urban squares. Temperature is explained by greenness, while holding built-up share, elevation and water fixed.
>
> The cooling slope is how much the temperature changes when greenness rises by 0.1. **A negative slope means greener squares are cooler.**
>
> Why the controls matter: this figure is Jodhpur. On the left, the raw relationship is weak, at minus 0.59, and not significant. Once we hold built-up share fixed, on the right, it becomes minus 1.32. The bare desert edge was hiding the effect, exactly as we saw on the last slide.
>
> We also treat neighbouring squares, in roughly 5 km blocks, as one unit when computing uncertainty, because nearby squares are alike.
>
> We fit one slope for every city, season and time of day. Because each fit compares squares *within* one city, that city's climate is held fixed.

*If asked whether this is causal:* no. It is an association, with built-up share, elevation and water held constant.

*If asked:* about 29,000 fits in total, including the robustness checks.

*Handover:* "Our climate teammate will explain how we describe each city's climate."

---

## Slide 11: Climate and people-weighting (Role 2)

> To ask *under what conditions* cooling is strongest, we need each city's climate. For that we use ERA5-Land. Its cells are about 9 km wide, too coarse to tell neighbourhoods apart. So we use it to describe the background climate each city sits in, one value per city per season.
>
> Our main measure of dryness is annual rainfall, with soil moisture as a second measure. We don't use potential evaporation, because ERA5's version is unreliable in dry areas.
>
> We also compute the Heat Index, which combines temperature and humidity. We compute it every day and then average, because averaging the inputs first would hide the hot afternoons.
>
> On the right is how we measure exposure. We weight each square's temperature by how many people live there, and compare that with the plain city average. If the gap is positive, people are living in hotter-than-average squares. My teammate will show those results later.

*If asked:* neither rainfall nor soil moisture can see irrigation, which matters because Manoli 2019 found that irrigated greening behaves differently.

*Handover:* "Now the results, starting with our pilot."

---

## Slide 12: Pilot (Role 3)

> We first tested the method on two cities at opposite ends of the climate range: Jodhpur, a desert city, and Kochi, a very wet one.
>
> In both, greener squares are clearly cooler by day. In Jodhpur, each 0.1 rise in greenness goes with 1.32 °C cooler surfaces. In Kochi, it is 1.04 °C. Both are clearly different from zero.
>
> The surprise was at night. In Jodhpur, greener squares are actually *warmer* at night, by 0.62 °C.
>
> *(optional)* In our final model, with elevation and water added, Jodhpur is minus 1.45 and Kochi minus 1.90. The direction never changes.
>
> So two cities showed the method works. Next, all 202 cities.

*If asked:* each dot is one square, with built-up share removed from both axes. The line's slope equals the regression result exactly.

*Handover:* "Our climate teammate will show how this changes with rainfall."

---

## Slide 13: Rainfall result (Role 2)

> This is our main test of conditions. Each dot is one city's cooling slope, plotted against its annual rainfall. The top row is daytime, the bottom row is night, and each column is a season.
>
> **By day, the line is flat.** Cooling does not depend on rainfall in any season. Before the monsoon the slope is 0.17, with a range from minus 0.73 to plus 1.07, which includes zero. Greener squares are about as much cooler in Jodhpur's climate as in Kochi's. So by day, our data supports neither side of the dry-climate debate.
>
> **At night, there is a clear pattern.** Wetter cities cool more, before the monsoon and after it. This sides with Guo and Schwaab: in drier places, the night-time benefit of greenery is weaker.
>
> *(optional)* The night pattern held in every version of the model we tried, including adding city size, air temperature and density.

*If asked:* the line is a regression across cities that gives more weight to cities with more precise slopes.

---

## Slide 14: Map (Role 2)

> Here is the daytime picture across India. Each circle is a city:
> - Blue means greener squares are cooler there, and red means warmer.
> - A hollow circle means the result is not statistically significant.
> - The size of the circle shows population.
>
> The map is overwhelmingly blue. 151 of 202 cities, three quarters, have significantly cooler green squares by day before the monsoon, and 191 have a negative slope. Only 2% go the other way, and they are scattered, with no region where greenery warms by day.
>
> The hollow circles are mostly small cities, where fewer squares give a less certain estimate. The 101 cities not shown are too small to estimate.

*If asked about a regional pattern:* there is none by day; the rainfall slide tests this formally.

---

## Slide 15: Dry cities vs Guo (Role 2)

> Let's compare directly with Guo's finding of 22% net warming in dry cities.
>
> We split our cities at 1,000 mm of rain, as Guo did. **By day, dry Indian cities behave just like wet ones.** About three quarters cool significantly, and none of the 56 dry cities warms.
>
> **At night it is different.** 38% of dry cities have warmer green squares at night, twice the share in wet cities. This falls steadily as rainfall rises: half of the cities under 750 mm, and only 3% above 1,500 mm. So Jodhpur's warm green nights are part of a dry-city pattern.
>
> Why don't we see Guo's daytime warming? Guo's dry cities are truly arid, while India's are semi-arid, and a lot of urban greenery here is watered, which rainfall data cannot see. Our method is also different, so this is a contrast, not a repetition of Guo's study.

*If asked whether 39 dry cities at night is enough:* with a looser 6-night cut-off we have 48 dry cities, and the result gets stronger, 54% against 18%.

*Handover:* "Next, what happens to the same city across seasons."

---

## Slide 16: Seasons (Role 3)

> This is our cleanest test of conditions, because we compare the **same squares in the same city** in different seasons. Everything fixed about the city, such as its layout, size and region, cancels out.
>
> By day, cooling gets **weaker** after the monsoon in 81% of 202 cities. At night it is the reverse: cooling gets **stronger** after the monsoon in 69% of cities.
>
> We expected wetter soils to explain this, but the change in soil moisture does not clearly explain it.
>
> *(optional)* One idea we have not tested yet: April and May have the most sun and the hottest surfaces, so there is more heat for vegetation to offset.

*If asked whether this could be noise:* across 202 cities the paired test gives p ≈ 7 × 10⁻¹⁹, and per city, 30% are significantly weaker and only 2% significantly stronger.

*Handover:* "Prajna will now show who actually gets this cooling."

---

## Slide 17: Exposure (Role 4)

> So far we have looked at squares. But heat exposure is about people. So we weighted each square by how many people live there, and compared that with the plain city average.
>
> **In 90 to 96% of cities, the crowded squares are less green than the city average.**
>
> At night, in 96 to 97% of cities, people live in hotter-than-average squares. By day the pattern is weaker but still in most cities, between 63 and 87% depending on the season.
>
> The right-hand chart shows why this matters. The less green a city's crowded squares are, the bigger their heat gap, with a strong correlation of minus 0.73.
>
> On average the gap is small, a few tenths of a degree, but in Kolkata it reaches over 1 °C.

*If asked whether 0.1 °C matters:* the point is the direction, almost every city at night, and the link to greenness. In some cities the gap is about 1 °C.

*If asked about income:* we used population density, not income, so we say "crowded", not "poor". Chakraborty et al. 2019 found poorer neighbourhoods hotter in 72% of 25 cities.

*Handover:* "Next, we checked whether water could explain any of this."

---

## Slide 18: Water check (Role 5)

> One worry: water is cool and has low greenness, so lakes and rivers could be mistaken for a vegetation effect. To check this, we measured how much of each square is covered by water in OpenStreetMap, and added it to the model.
>
> It barely changes anything. The typical daytime slope moves from minus 1.05 to minus 1.13, so the cooling effect slightly strengthens. Jodhpur's warm green nights are exactly the same with and without water, at 0.94, so water does not cause them.
>
> One known gap: OpenStreetMap draws the sea as a coastline, not as water area. So squares that are partly sea are not counted.

*If asked how water share was calculated:* we overlaid OpenStreetMap water polygons on the exact footprint of each satellite square.

---

## Slide 19: Robustness (Role 3)

> Finally, we checked whether our answer depends on our choices. We re-ran everything:
> - with a different greenness index
> - with a stricter definition of urban
> - without each control
> - without water squares
> - with a looser night cut-off
>
> The daytime result holds every time: 70 to 77% of cities cool significantly by day in every version.
>
> The choice that matters most is the controls. Without them, the ranking of cities changes a lot, which is why we always hold built-up share, elevation and water fixed. Removing the water control changes very little.
>
> *(optional)* The rainfall slope changes sign across versions and is never significant, which supports our reading of no clear daytime rainfall pattern.

*If asked why NDVI and EVI disagree in some cities:* they differ on significance in 14% of cities, and we have not explained that yet.

*Handover:* "Prajna will sum up what we've found."

---

## Slide 20: Observations (Role 4)

> To sum up, against each hypothesis:
>
> - **H1, yes:** greener is cooler by day almost everywhere, in three quarters of cities.
> - **H2, not by day:** daytime cooling does not depend on rainfall, and no dry city warms by day, unlike Guo's 22%.
> - **H3, yes, at night:** wetter cities cool more, and dry cities often have warmer green squares.
> - **H4, yes:** within the same city, the monsoon weakens daytime cooling and strengthens night cooling.
> - **H5, yes:** people live where it is less green and hotter, especially at night.
>
> Our main data limits are no monsoon season and 101 cities too small to estimate, and controlling for water barely changed anything.
>
> All of these are associations, not proof of cause.

*Handover:* "Our teammate will close with limitations and next steps."

---

## Slide 21: Next steps and limitations (Role 5)

> We are about halfway through the project, with the core results in place.
>
> For the final submission, we plan four things:
> 1. Our main next step is H6: turning surface temperature into the heat people actually feel, using the Heat Index and the surface-to-air ratios from the literature.
> 2. A measure of who receives the cooling.
> 3. Building height as an extra control.
> 4. A detailed Hyderabad case study at 30 m resolution.
>
> We are also clear about our limits:
> - We measure surface temperature, not the heat people feel.
> - Climate is one value per city.
> - Results are associations.
> - There is no monsoon season, and there is less night data for humid cities.
> - OpenStreetMap misses the sea.
> - Greenness cannot tell trees from grass or crops.
>
> To answer our question in one line: greenery cools Indian cities by day almost everywhere, and the conditions that matter show up at night and between seasons. Thank you.
