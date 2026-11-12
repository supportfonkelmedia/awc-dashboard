/**
 * Tekst uit de config staat soms in hoofdletters ("FINANCIËLE GEZONDHEID").
 * Op het scherm tonen we gewone zinsletters; afkortingen blijven staan.
 */
const AFKORTINGEN = new Set([
    'MT', 'KPI', "KPI'S", 'AWC', 'AFC', 'ACC', 'OTIF', 'EBITDA', 'LOB', 'ENPS', 'HR', 'B2B',
]);

export function leesbaar(tekst) {
    if (tekst == null) {
        return '';
    }
    const s = String(tekst).trim();
    const letters = s.replace(/[^\p{L}]/gu, '');
    if (letters.length < 2 || s !== s.toLocaleUpperCase('nl-NL')) {
        return s;
    }

    const woorden = s.split(/(\s+)/).map((w) =>
        AFKORTINGEN.has(w.replace(/[^\p{L}']/gu, '')) ? w : w.toLocaleLowerCase('nl-NL'),
    );
    const zin = woorden.join('');

    return zin.charAt(0).toLocaleUpperCase('nl-NL') + zin.slice(1);
}
