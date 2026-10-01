import type { NameStyleId } from '../types/nation';

export interface NameStyle {
  prefixes: string[];
  suffixes: string[];
  /** Complete names used occasionally for variety. */
  whole: string[];
}

/**
 * Place-name building blocks. Names are invented from these fragments so the
 * map feels historical without copying real geography.
 */
export const NAME_STYLES: Record<NameStyleId, NameStyle> = {
  english: {
    prefixes: ['Ash', 'Brack', 'Chester', 'Dun', 'Elm', 'Fair', 'Glen', 'Hart', 'Kings', 'Lang', 'Marl', 'North', 'Oak', 'Pen', 'Red', 'Stan', 'Thorn', 'Wex', 'Bram', 'Cold', 'Hol', 'Mill', 'New', 'Rother', 'Sel', 'Wey', 'Brad', 'Hay', 'Cam', 'Dor'],
    suffixes: ['ford', 'ham', 'ton', 'bury', 'wick', 'field', 'by', 'stead', 'mouth', 'ley', 'worth', 'gate', 'well', 'combe', 'dale', 'minster', 'hurst', 'chester'],
    whole: ['Kingsbridge', 'Highcliff', 'Redmarsh', 'Thornwood'],
  },
  french: {
    prefixes: ['Belle', 'Mont', 'Fontaine', 'Beau', 'Clair', 'Roche', 'Val', 'Chateau', 'Ver', 'Cor', 'Lor', 'Sar', 'Bel', 'Mar', 'Haute', 'Plan', 'Neuf', 'Pont', 'Sainte-Mar', 'Saint-Val', 'Lan', 'Vic', 'Cha', 'Bri'],
    suffixes: ['court', 'ville', 'mont', 'ac', 'lieu', 'fort', 'eux', 'bourg', 'ais', 'oise', 'ennes', 'lac', 'champ', 'ière', 'y'],
    whole: ['La Haye Blanche', 'Plaine-sur-Lys', 'Mont-Valois', 'Belle-Étoile', 'Le Galet', 'Hougard'],
  },
  german: {
    prefixes: ['Rothen', 'Stein', 'Linden', 'Ober', 'Unter', 'Wald', 'Eisen', 'Hohen', 'Kirch', 'Schwarz', 'Weiss', 'Gruen', 'Falken', 'Adler', 'Rosen', 'Neu', 'Alt', 'Konigs', 'Mark', 'Wolfen', 'Brand', 'Lands'],
    suffixes: ['burg', 'dorf', 'berg', 'stadt', 'feld', 'hausen', 'heim', 'bach', 'au', 'tal', 'wald', 'brück', 'hof', 'stein', 'furt'],
    whole: ['Wavrenfeld', 'Ligenau', 'Bülowshof', 'Frischenberg', 'Ohlen'],
  },
  dutch: {
    prefixes: ['Amster', 'Rotter', 'Gro', 'Lei', 'Zwol', 'Haar', 'Dor', 'Ven', 'Zee', 'Bre', 'Til', 'Hil', 'Alk', 'Ut', 'Mid', 'Del'],
    suffixes: ['dam', 'ningen', 'den', 'le', 'lem', 'drecht', 'lo', 'land', 'burg', 'hoven', 'veen', 'sum', 'maar'],
    whole: ['Nieuwpoort', 'Zeeburg', 'Waterhaven'],
  },
  slavic: {
    prefixes: ['Novo', 'Staro', 'Belo', 'Krasno', 'Volo', 'Yaro', 'Vladi', 'Smo', 'Tver', 'Kalu', 'Ozer', 'Lipo', 'Svetlo', 'Bor', 'Kur', 'Pere', 'Zor', 'Mir'],
    suffixes: ['grad', 'gorod', 'sk', 'ovo', 'evo', 'insk', 'avl', 'mir', 'slavl', 'ets', 'ino', 'osk'],
    whole: ['Velikiye Polya', 'Krasnaya Gorka', 'Belaya Reka'],
  },
  spanish: {
    prefixes: ['San', 'Villa', 'Alta', 'Torre', 'Monte', 'Puerto', 'Sierra', 'Val', 'Cala', 'Mira', 'Sala', 'Cor', 'Alcan', 'Bena', 'Gua'],
    suffixes: ['dolid', 'manca', 'doba', 'mera', 'flores', 'ranca', 'lejo', 'tara', 'via', 'nueva', 'real', 'jara', 'zar'],
    whole: ['Puerto Real', 'Castillo Alto', 'Vega Dorada'],
  },
  nordic: {
    prefixes: ['Upp', 'Norr', 'Stock', 'Gote', 'Lin', 'Vas', 'Ore', 'Kal', 'Hels', 'Jon', 'Karl', 'Falu', 'Sund', 'Ystad', 'Skel', 'Lule'],
    suffixes: ['sala', 'köping', 'holm', 'borg', 'by', 'vik', 'stad', 'ström', 'å', 'fors', 'berga', 'lund'],
    whole: ['Nordhavn', 'Isfjord', 'Kvarnby'],
  },
  turkish: {
    prefixes: ['Kara', 'Ak', 'Sari', 'Kizil', 'Yeni', 'Eski', 'Demir', 'Bey', 'Gol', 'Ala', 'Kus', 'Tep', 'Ordu', 'Bur', 'Mar'],
    suffixes: ['köy', 'hisar', 'su', 'kale', 'pazar', 'dere', 'tepe', 'şehir', 'ova', 'yurt', 'abad', 'kent'],
    whole: ['Altinkale', 'Yildizhisar', 'Denizkent'],
  },
  polish: {
    prefixes: ['Kra', 'Wro', 'Lub', 'Rad', 'Byd', 'Tor', 'Ostro', 'Zam', 'Gnie', 'Pło', 'Chełm', 'Sie', 'Biel', 'Now'],
    suffixes: ['ków', 'cław', 'lin', 'om', 'goszcz', 'uń', 'łęka', 'ość', 'zno', 'ck', 'dlce', 'sk', 'y Sącz'],
    whole: ['Biała Wieś', 'Zielona Góra Mała'],
  },
  generic: {
    prefixes: ['Grey', 'Stone', 'Iron', 'Wind', 'River', 'Moor', 'Frost', 'Sun', 'Raven', 'Wolf', 'Fox', 'Ember', 'Silver', 'Golden'],
    suffixes: ['hold', 'march', 'reach', 'fell', 'moor', 'watch', 'crossing', 'vale', 'haven', 'keep'],
    whole: ['The Marches', 'Free Cantons', 'Highlands'],
  },
};
