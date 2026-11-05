F = 'https://www.rebornevo.com/forums/topic/'
ORDER_HTML = '''
<section aria-labelledby="order">
  <h2 id="order">Battle order <span class="tag">lead, mid, closer</span></h2>
  <div class="two">
    <div class="box">
      <h3>Doubles (Texen, Crawli, Eli &amp; Sharon, Geara &amp; Zetta, Giratina)</h3>
      <div class="tablewrap"><table>
        <thead><tr><th>Role</th><th>Pair</th><th>Job</th></tr></thead>
        <tbody>
          <tr><td><strong>Lead</strong></td><td>Annihilape + Leavanny-Aevian</td><td>Your two fastest. Intimidate on entry, then Close Combat or Shadow Punch the Dark mons and Typhlosion before Eruption fires at full HP.</td></tr>
          <tr><td><strong>Mid</strong></td><td>Rhyperior + Gholdengo</td><td>Rhyperior's boosted Stone Edge handles Fire and Flying. Gholdengo covers Ghost and Fairy and ignores status.</td></tr>
          <tr><td><strong>Closer</strong></td><td>Golisopod-Aevian + Glaceon</td><td>Glaceon's Icy Wind slows what's left, then Golisopod uses Swords Dance and sweeps with Skill Link Bone Rush.</td></tr>
        </tbody>
      </table></div>
    </div>
    <div class="box">
      <h3>Singles and per-fight changes</h3>
      <ul>
        <li><strong>Singles default:</strong> lead Annihilape. Mid Rhyperior, Gholdengo and Leavanny. Close with Golisopod, plus Glaceon when you need speed control.</li>
        <li><strong>Texen</strong> (you bring 3): Gholdengo, Annihilape and Golisopod. Make It Rain is 1.5x and Swords Dance is +3 on Big Top.</li>
        <li><strong>Groudon:</strong> lead Glaceon (Freeze-Dry, Blizzard). Leave Gholdengo out, because Earthquake does about 185% to it.</li>
        <li><strong>Eli &amp; Sharon:</strong> lead Rhyperior + Gholdengo. Honchkrow's Brave Bird one-shots Annihilape on Mountain.</li>
        <li><strong>Amber:</strong> swap Whiscash or Jellicent in for Glaceon and lead Rhyperior. A forum tip: Bounce turns Concert Venue into Sky Field, which kills her boosts. The Bounce tutor is in Akuwa Town this chapter.</li>
      </ul>
    </div>
  </div>
</section>'''

COMMUNITY = f'''
<section aria-labelledby="comm">
  <h2 id="comm">What players say <span class="tag">Reborn Evolved forums</span></h2>
  <p class="legend">Read directly from the official Rejuvenation forums (rebornevo.com). Reddit couldn't be added to this session's network allowlist; the environment service refused it. Dates show which game version each post is about. V14 came out in 2025.</p>
  <div class="two">
    <div class="box">
      <h3>Mons on your team</h3>
      <ul>
        <li><strong>Aevian Golisopod:</strong> "THE MVP" of a V14 endgame team built to beat Madame X without cheese (<a href="{F}80802-list-your-endgame-v14-team-that-wasnt-made-just-to-cheese-v14-spoilers/">Nov 2026</a>). Another player: "tank like a champ and hit like a truck" (<a href="{F}66111-best-aevian-pokemon/">2023</a>). One complaint: the occasional miss on Pin Missile or Bone Rush (<a href="{F}66198-taking-suggestions-for-new-pokemon-members/">2023</a>).</li>
        <li><strong>Aevian Lapras:</strong> praised for using No Guard with Sing, Zap Cannon and Stone Edge, which never miss. At cap 55 you don't have Stone Edge yet, which is why it's on the bench.</li>
        <li><strong>Aevian Musharna:</strong> "decent if you get it early", Tough Claws Play Rough and Throat Chop, a good Trick Room setter later (<a href="{F}66111-best-aevian-pokemon/">2023</a>).</li>
        <li><strong>Pixilate Sylveon / Mega Gardevoir Hyper Voice</strong> is called "a horror for Double Battles" (<a href="{F}66727-listing-of-pokemon-i-found-especially-strong-for-end-game/">2023</a>).</li>
      </ul>
    </div>
    <div class="box">
      <h3>Mons in your boxes players rate highly</h3>
      <ul>
        <li><strong>Hisuian Electrode:</strong> "breaks the midgame" and is "really helpful during the Terajuma arc" (<a href="{F}66727-listing-of-pokemon-i-found-especially-strong-for-end-game/">2023</a>). You own one, and the Electrode Crest is on Route 6 this chapter.</li>
        <li><strong>Shadow Cacturne:</strong> "used it the entire playthrough". Obstruct plus 115 Atk Sucker Punch, Fake Out, Spikes (<a href="{F}66727-listing-of-pokemon-i-found-especially-strong-for-end-game/">2024</a>). You have the purified one, with Fake Out and Obstruct.</li>
        <li><strong>Aevian Froslass:</strong> "a demon". One player says Adaptability Muddy Water "carried me" through the cloned-Adam Escavalier fight on Deep Earth, which is in Chapter 8. You need a female Aevian Snorunt; yours is male.</li>
        <li><strong>Multiscale Dragonite, Garchomp, Toxapex, Mamoswine</strong> come up again and again as strong all-rounders. You own a Mamoswine.</li>
      </ul>
    </div>
    <div class="box">
      <h3>Crests</h3>
      <ul>
        <li>The most-praised crests (Delcatty, Bastiodon, Feraligatr) all come after Chapter 8 (<a href="{F}61826-which-is-overall-strongest-pokemon-in-rejuvenation-your-opinion/">2022</a>, <a href="{F}66198-taking-suggestions-for-new-pokemon-members/">2023</a>). The Feraligatr Crest is a Chapter 9 Virtual League reward, and you're missing Totodile.</li>
        <li>A player's full crest guide suggests crested <strong>Zoroark copying Nidoking</strong>, which gets Sheer Force with Night Daze and Sludge Bomb STAB (<a href="{F}66015-using-crest-pokemon-as-god-intended/">2023</a>). The Zoroark Crest is in Garufa Sanctuary this chapter.</li>
      </ul>
    </div>
    <div class="box">
      <h3>Fight tips from players</h3>
      <ul>
        <li><strong>Amber:</strong> use Bounce (Akuwa Town tutor) to turn the field into Sky Field and shut off her boosts. A player adds that it "can also work against Zetta &amp; Geara" (<a href="{F}58916-easy-method-to-bully-the-amber-fight-without-making-her-mad/">2022</a>).</li>
        <li><strong>Geara &amp; Zetta:</strong> players describe winning "after quite a few tries" (<a href="{F}74192-spoiler-a-thought-on-the-battle-for-mount-valor/">2024</a>). Typhlosion's Eruption is the threat to remove first.</li>
        <li><strong>Deep Earth's Gravity</strong> boosts accuracy, which players lean on in the Garufa fights.</li>
      </ul>
    </div>
  </div>
</section>'''

CHECKLIST = '''
<section aria-labelledby="check">
  <h2 id="check">Chapters 1–7 collection check</h2>
  <p class="legend">Every wild table, Rift Den, gift, static encounter, egg and trade in the walkthrough's Chapter 1–7 sections, checked against your 406. Each evolution family counts once, and regional or Aevian forms count separately. Pick-one choices count if you have any option.</p>
  <div class="tablewrap"><table>
    <thead><tr><th>Missing</th><th>Where / how (from the walkthrough)</th><th>Worth getting?</th></tr></thead>
    <tbody>
      <tr><td><strong>Galarian Yamask</strong></td><td>Wild in Wispy Ruins, Backstage Theatre and Wispy Chasm caves (Goldenleaf).</td><td>Yes for the dex. Its evolution, Runerigus, needs a damage-taken method.</td></tr>
      <tr><td><strong>Mystery Egg</strong> (1 of 21)</td><td>Route 3 market, daytime: trade your Phantump egg to the boy. It's fixed by your save file and could be Togepi, Axew, Pawniard, Larvesta, Aevian Litwick, Tyrunt and others. None of the 21 are in your boxes.</td><td>Yes. Several hatches are strong (Axew, Larvesta, Pawniard).</td></tr>
      <tr><td><strong>Minccino</strong></td><td>Chrisola Hotel: take the old lady's quest, beat the grunts in Gearen Park, then battle and catch it.</td><td>Dex only.</td></tr>
      <tr><td><strong>Throh</strong></td><td>Sheridan Village, south side: talk to the woman to catch it. The daycare trainer trades a Sawk for it.</td><td>Optional. Players rate Wide Guard users in doubles.</td></tr>
      <tr><td><strong>Fidough</strong></td><td>Route 3, next to the camper: give it a Gourmet Treat.</td><td>Dex only.</td></tr>
      <tr><td><strong>Galarian Corsola</strong></td><td>Mynori Sea dock: wait for it to wander up.</td><td>Dex only (Cursola needs a later method).</td></tr>
      <tr><td><strong>Totodile</strong></td><td>Chrisola Hotel basement, at night: Surf to the dark patch and use a Gourmet Treat.</td><td><strong>Yes.</strong> The Feraligatr Crest (Chapter 9) is called "basically a mega" by players.</td></tr>
      <tr><td><strong>Aevian Froslass</strong> (form)</td><td>Needs a <strong>female</strong> Aevian Snorunt (Mt. Terajuma, near the Weather Institute) and a Water Stone. Yours is male.</td><td><strong>Yes.</strong> A community favourite with Adaptability.</td></tr>
    </tbody>
  </table></div>
  <p class="legend">Not counted as missing: <strong>Spiritomb</strong> needs the Odd Keystone from Griselda's Treasure 7, which comes after Chapter 7. The <strong>Poliwag quest</strong> finishes in Chapter 8 (Poliwag #6 is on Route 6). The Route 2 egg (you have Skiddo and Mudbray), C's egg (Blipbug) and the Aevian Mystery Egg (Aevian Wimpod) are all covered.</p>
  <div class="two">
    <div class="box">
      <h3>Crests and Mega stones</h3>
      <ul>
        <li><strong>All found:</strong> Ariados Crest (Griselda's Treasure 2), Whiscash Crest (Treasure 3), Furret Crest (Tesla's yacht), Meowsticite, Chandelurite.</li>
        <li><strong>Can't confirm from your export</strong> (bag items don't show): Cairo's Red Essence Shop on Route 4 sells the Noctowl, Minun, Plusle, Simisage, Simisear and Simipour Crests (2,000 each) and the Thievul Crest (5,000). You own Minun, Plusle, Simipour, Simisear and Thievul. None of them make the six, so these are optional.</li>
        <li><strong>Not missed:</strong> the Fearow Crest (Treasure 7) and Dedenne Crest (Treasure 8) come after Chapter 7. The Vespiquen Crest needs all 9 treasures.</li>
      </ul>
    </div>
    <div class="box">
      <h3>Moves now allowed</h3>
      <ul>
        <li><strong>71 TMs/HMs</strong> obtainable in Chapters 1–7. Highlights: Shadow Ball, X-Scissor, Dragon Claw, Rock Tomb, Dig, Bulldoze, Surf, Elemental Fangs, Power-Up Punch, Low Sweep, Hex, Brutal Swing. Trick Room (TM92), Earthquake, Rock Slide and Stone Edge TMs come later.</li>
        <li><strong>Tutors at 7 badges:</strong> Luck's Tent Marshie, Margo, Marvin and Marnie (7-badge tier), Wispy Shop and the Kakori Beach tutor. The Akuwa Town tutors (including Bounce) open in Chapter 8.</li>
        <li>Move Relearner moves are still excluded under your rules.</li>
      </ul>
    </div>
  </div>
</section>'''
