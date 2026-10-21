# A section's video link must land at the topic block's START, not at the sub-item whose title matches best

**Symptom** Reader feedback on vol 1 §2.1.2 ("simplest properties of convergent
sequences"): "հղումը տանում ա հատկություն 4-ի վրա" - the link opened the lecture at
Property 4 (t=1833) while the book section begins with Property 1 (the lecture's t=0).

**Cause** Both the scorer and the human curator (me) picked the timestamped topic
whose TITLE was most similar to the heading. But a lecture's chapter list names each
sub-item (Property 2, Property 3, a proof, a closing example) and often has no entry
named like the section itself, so the best title match is routinely a mid-block item.
The right target is where the block STARTS - which may be t=0, a block header
("Հատկություններ", "Հորիզոնական ասիմպտոտ"), or the first item of the sequence.

**Consequences** A sweep of all placeable matches for continuation-marker topics
(Հատկություն N>1, Ապացույց, Օրինակ, Դիտողություն, Հետևանք, Մասնավոր դեպք - and a
second pass for bare "Հատկություն", which the first regex missed because
"Հատկություն․ 1 ֆունկցիայի ինտեգրալը" has no sequence number) flagged 9 of 388.
Verdicts, each checked against the lecture's full chapter list:

- 6 retimed to the block start: 2.1.2 (t=1833→0), 2.5.6 (1949→994), 4.7.9
  (4020→3114), 5.4 both lecturers (3045→400, 3170→2672), 17.3 (3045→400).
- 1 dropped: 9.4.4 Cauchy product - the channel has NO Cauchy-product content; the
  linked "Օրինակ 2․ արտադրյալներից կազմված շարք" is a d'Alembert ratio-test example
  whose terms happen to be products. No link beats a wrong link (policy of ch 15/16/19).
- 2 were data-hygiene only (13.1, 18.1 sit on chapter-card pages, lines never ship).
- 18.4.2 kept: the "Հետևանք" it targets IS the heading's own statement.

All fixes went through manual_matches.json overrides (scorer output is regenerated,
never hand-edited). Lesson for future matching: score candidate topics by title, but
then walk BACKWARD in the same video's chapter list to the start of the containing
block before emitting the timestamp.
