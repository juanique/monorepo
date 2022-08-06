\version "2.20.0"
\header {
  title = "Valsesito"
  composer = "Subhira"
  % Do not display the default LilyPond footer for this book
  tagline = ##f
}
\score {
  \new PianoStaff <<
    \new ChordNames {
      \set chordChanges = ##t
      \chordmode {
         gis2.:m|gis:m|gis:m|gis:m|
         fis:6|fis:6|fis:6|fis:6|
         gis2.:m|gis:m|gis:m|gis:m|
         fis:6|fis:6|fis:6|fis:6|
         e
      }
    }
    \new Staff \relative {
      % \tempo "Andante"
      \tempo  4 = 110
      \time 3/4
      \key b \major
      ais'2.~ |
      ais2.~ |
      ais2.~ |
      ais2 \grace {dis,16(} cis'4)|
      \grace {cis,16(} ais'2.~) |
      ais2.~ |
      ais2.~ |
      ais4 ais cis|
      ais2.~ |
      ais2. |
      \grace {ais16(} ais'2.) |
      b,4 cis dis |
      ais2. |
      \grace {gis16(} gis'2.)~ |
      gis2. |
      r8 <cis,, fis> <dis gis> <fis ais> <gis b> <ais cis> |
      <gis b>2. |
      <gis, cis fis>2. |
      r4 gis'8 ais b cis dis e dis4 cis |
      cis2. |
      b2  ais4|
      gis2.~ |
      gis4 fis gis |
      \grace {ais16(} ais'2.) |
      \grace {ais,16(} ais'2.) |
      \grace {ais,16(} ais'2.) |
      \grace {ais,16(} ais'4) \grace {b,16(} b'4) \grace {cis,16(} cis'4) |
      \grace {gis,16(} gis'2.) |
      \grace {ais,16(} ais'4.) ais,8 gis4 |
      gis2. |
      r8 ais ais' ais, ais' ais,
      ais'2. |
    }
    \new Staff \relative {
      \clef "bass"
      \key b \major
      gis,8( dis' ais' <b dis> <cis fis> <dis gis>) |
      gis,,8( dis' ais' <b dis> <cis fis> <dis gis>) |
      gis,,8( dis' ais' <b dis> <cis fis> <dis gis>) |
      gis,,4 dis' b' |
      fis,8( cis' gis' <ais dis> <cis fis> <dis gis>) |
      fis,,8( cis' gis' <ais dis> <cis fis> <dis gis>) |
      fis,,8( cis' gis' <ais dis> <cis fis> <dis gis>) |
      fis,,4 cis' gis'
      gis,8( dis' ais' <b dis> <cis fis> <dis gis>) |
      gis,,8( dis' ais' <b dis> <cis fis> <dis gis>) |
      gis,,8( dis' ais' <b dis> <cis fis> <dis gis>) |
      gis,,8( dis' ais' <b dis> <cis fis> <dis gis>) |
      fis,,8( cis' gis' <ais dis> <cis fis> <dis gis>) |
      fis,,8( cis' gis' <ais dis> <cis fis> <dis gis>) |
      fis,,8( cis' gis' <ais dis> <cis fis> <dis gis>) |
      fis,,8( cis' gis' <ais dis> <cis fis> <dis gis>) |
      e,,8 b' e <gis cis>8 <ais dis> <cis fis> |
      e,,4 b' e |
      e,8 b' e gis ais cis dis4 fis dis |
      gis,,8( dis' ais' <b dis> <cis fis> <dis gis>) |
      gis,,8( dis' ais' <b dis> <cis fis> <dis gis>) |
      gis,,8( dis' ais' <b dis> <cis fis> <dis gis>) |
      gis,,8( dis' ais' <b dis> <cis fis> <dis gis>) |
      gis,,8( dis' ais' <b dis> <cis fis> <dis gis>) |
      gis,,8( dis' ais' <b dis> <cis fis> <dis gis>) |
      gis,,8( dis' ais' <b dis> <cis fis> <dis gis>) |
      gis,,4 dis' b' |
      fis,8( cis' gis' <ais dis> <cis fis> <dis gis>) |
      fis,,8( cis' gis' <ais dis> <cis fis> <dis gis>) |
      fis,,8( cis' gis' <ais dis> <cis fis> <dis gis>) |
      fis,,8( cis' gis' <ais dis> <cis fis> <dis gis>) |
      gis,,8( dis' ais' <b dis> <cis fis> <dis gis>) |
    }
  >>
  \layout {}
  \midi {}
}
