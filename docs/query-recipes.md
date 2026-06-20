# Query Recipes

Queries are used in RapidCull when creating virtual galleries and collection views. Each expression filters photo and video records by metadata fields such as person, date, camera, lens, exposure settings, and keywords.

---

## By Person

Match all images tagged with a specific person.
```
person=alice
```

Match images containing either of two people.
```
person=alice OR person=bob
```

Match images with all three people present.
```
person=alice AND person=bob AND person=carol
```

Exclude images tagged with a specific person.
```
NOT person=alice
```

---

## By Date

Match images captured on a single exact date.
```
date=2024-06-15
```

Match all images captured during a full calendar year.
```
date>=2024-01-01 AND date<2025-01-01
```

Match all images captured during a single month.
```
date>=2024-06-01 AND date<2024-07-01
```

Match images captured on or after a specific date.
```
date>=2024-06-01
```

Match images captured before a specific date.
```
date<2024-01-01
```

---

## By Camera & Lens

Match images from an exact camera body (case-insensitive).
```
camera=Sony A7R V
```

Match images from any camera whose model contains a substring (useful for brand or series matching).
```
camera~Canon
```

Match images from any Sony camera.
```
camera~Sony
```

Match images shot with a lens whose model contains a focal length or name substring.
```
lens~85mm
```

Match images shot with any prime in the 50mm range.
```
lens~50mm
```

---

## By Exposure Settings

Match low-ISO shots (clean, low-noise exposures).
```
iso<=400
```

Match high-ISO shots (typically low-light or action situations).
```
iso>=1600
```

Match images shot wide open or near wide open.
```
fnumber<=1.8
```

Match images shot at a typical portrait aperture or wider.
```
fnumber<=2.8
```

Match images stopped down for depth of field (landscape or architecture).
```
fnumber>=8
```

Match telephoto shots (200mm or longer).
```
focal>=200
```

Match wide-angle shots (under 35mm).
```
focal<35
```

Match a standard prime range (around 50mm).
```
focal>=45 AND focal<=55
```

---

## By Keyword

Match images tagged with an exact keyword.
```
keyword=portrait
```

Match images tagged as blurred (useful for finding rejects).
```
keyword=blurred
```

Match images where any keyword contains a substring (e.g., all studio-related tags).
```
keyword~studio
```

Match images tagged for events.
```
keyword=event
```

---

## Combined Queries

Match images of a person taken within a specific year.
```
person=alice AND date>=2024-01-01 AND date<2025-01-01
```

Match portrait shots of a specific person taken with fast glass.
```
person=alice AND fnumber<=2.8 AND keyword=portrait
```

Match clean Sony shots taken from a specific date onward.
```
camera~Sony AND iso<=800 AND date>=2024-06-01
```

Match event images featuring either of two people.
```
(person=alice OR person=bob) AND keyword=event
```

Match telephoto portraits taken at low ISO.
```
focal>=135 AND fnumber<=2.8 AND keyword=portrait AND iso<=800
```

Match images from a specific camera body during a single month.
```
camera=Sony A7R V AND date>=2024-09-01 AND date<2024-10-01
```

---

## Exclusion Patterns

Match images that are not blurred and were taken at low ISO.
```
NOT keyword=blurred AND iso<=800
```

Match a person's images that have not been marked as rejects.
```
person=alice AND NOT keyword=reject
```

Match images of either person that are not blurred.
```
(person=alice OR person=bob) AND NOT keyword=blurred
```

Exclude images shot at very high ISO (for a clean-shots gallery).
```
NOT iso>=3200
```

Match wide-aperture shots that are not marked reject or blurred.
```
fnumber<=2.0 AND NOT keyword=reject AND NOT keyword=blurred
```
