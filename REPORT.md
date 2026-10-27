# Assignment 2 Report

*Delete this italic guidance as you fill in each section. You'll be asked to
defend any of this without your code in front of you. Write only what you
can actually explain.*

- **Name**: Isabella Lentini
- **Student ID**: 20211
- **Email**: ilentini.ieu2022@student.ie.edu
- **Group**: BBADBA 5B

## Business problem, and the cost of being wrong

The decision is whether a worker can walk onto a construction site or has to be
stopped because they are not wearing a hard hat. I am thinking of a medium site
of around 300 workers, where everyone goes through one entrance gate, usually
twice a day (in the morning and after lunch). That is about 600 gate passes a
day. Right now a gate supervisor checks this by eye, which means someone has to
stand there and watch every person that walks in.

A camera at the gate takes a picture of each worker, and the model looks for a
head without a hard hat. One gate pass is one case. I treat "worker without a
hard hat" as the positive class, because that is the thing the site wants to
catch. There are three possible outcomes: the worker is let in, the worker is
stopped, or, when the model is not sure, the snapshot is sent to the gate
supervisor's tablet. Checking a snapshot takes about 10 to 15 seconds.

The two mistakes do not cost the same. A false positive means stopping a worker
who is actually wearing a hard hat. They lose maybe a minute, and the supervisor
loses some time too, so I think this costs around 1 to 2 euros. Of course, if it
happens too often, workers will start ignoring the system, so false alarms are
not free. A false negative means letting someone in without a hard hat. Most of
the time nothing happens, but if something falls on them it can be a serious
head injury, with sick leave, insurance and legal costs, and the company can
also be fined by the labour inspectorate. Even taking into account that an
accident on any single day is unlikely, I believe a miss costs around 50 times
more than a false alarm, so roughly 50 to 100 euros per case. I set the exact
figures, and where they come from, in the cost section.

At a site in the EU with an entrance check, I expect about 3 out of 100 workers
to show up without a hard hat, mostly because they forget it after a break. So
positives are rare, which means that if the threshold is too low, most alerts
will be false alarms.

This asymmetry drives the rest of the project. Since a miss is much worse than a
false alarm, I care more about recall on the "no hard hat" class than about
precision, the threshold should be on the low side, and uncertain cases should
go to the supervisor instead of being let through.

## Dataset

I use the Hard Hat Workers dataset from Roboflow Universe:

- **Workspace**: joseph-nelson
- **Project**: hard-hat-workers
- **Version**: 5
- **Link**: https://universe.roboflow.com/joseph-nelson/hard-hat-workers/dataset/5
- **License**: public domain

It is an object detection dataset. Each image is a photo of one or more
workers, mostly on construction sites, and every head has a box around it.
There are two classes: `helmet`, a head wearing a hard hat, and `head`, a head
without one. The original project also has a `person` class, but version 5
drops it. That works for me, since it only has 615 instances and does not help
the decision. I picked version 5 because it has no augmentation baked in, so
the test images are real photos. I stayed away from version 14, which relabels
every helmet as a head and would make my problem impossible to learn.

This dataset serves the problem because what it labels is exactly what the
gate has to decide: is there a head without a hard hat. `head` is my positive
class. To turn boxes into one decision per case, I count an image as positive
if the model finds at least one `head` above the threshold, and negative
otherwise.

The main difference from my problem is the camera angle. I mean, most photos
show part of a site from a distance with several people in them, while a camera
at the gate would see one person close up. I come back to this in the next
section.

## What the dataset's composition implies

| Split | Images | `head` (no hard hat) | `helmet` | Images with at least one `head` |
|---|---|---|---|---|
| Train | 4,916 | 4,612 | 13,919 | 911 (18.5%) |
| Valid | 1,413 | 1,339 | 3,913 | 256 (18.1%) |
| Test | 706 | 726 | 1,915 | 140 (19.8%) |

I computed these from the label files. The split is about 70/20/10. There are
about three helmets for every bare head, so `head` is the minority class, but
with 726 instances in test I think it is still big enough for its per-class
precision and recall to mean something. The number that worries me more is at
the image level, since that is what my decision runs on: only 140 test images
have a bare head in them. So one missed image moves recall by 0.7 points, and
the margin of error is about 2.5 points either way. Differences between
thresholds smaller than that are just noise.

The objects are very small. The images are around 500 by 333 pixels, and the
median `head` box covers 0.6% of the image, so about 32 by 32 pixels, with 72%
of them under 1%. On top of that, the scenes are crowded: a median of 3 heads
per image and up to 35. A positive image has about 5 bare heads on average.

This has three consequences. First, the test set has a bare head in 19.8% of
the images, while I expect 3% at the gate. So I cannot take precision from the
test set as it is, since with fewer positives there will be more false alarms
for every real catch. Instead, I use the true positive and false positive rates
from the test set and reweight them with my 3% base rate in the cost section.
Second, in the test set a positive image usually has several bare heads, so the
model only needs to find one of them to get the image right. At the gate there
is one person and one head, so I believe the image-level recall I measure is
optimistic. Third, the model learns from small heads seen from far away, while
at the gate a head fills a big part of the frame. All three splits come from
the same source, so the test set looks like the training data, not like my
camera. In the end, my numbers show how well the model does on this kind of
photo, not how it will do at a real gate. To know that, I would need to test it
on photos taken at an actual entrance.

## Finetuning and baselines

*Which model and task (detection or classification) and why. A results table on
the same test split: your finetuned model, the pretrained COCO model zero-shot,
and a trivial baseline. What changed, and whether the gap is as large as you
expected.*

## Per-class evaluation and failure modes

*Per-class AP50, or per-class precision/recall and the confusion matrix.
Which class carries the headline number, which one is dragging, and what the
model actually confuses with what. Show where it breaks, not just that it
works.*

## Cost matrix and operating point

*Your euro cost for each kind of error and where each figure came from. The
base rate you assumed. The cost-against-threshold sweep, and the operating
point you chose. State the assumption that would most change your answer if it
were wrong.*

## What a person still has to check

*Your two thresholds, and what share of cases they send to a person. How many
that is per day, how long one takes to check, and how many people that needs.
Is that realistic? Then your design priced against the three alternatives:
doing nothing, having a person check everything, and letting the model decide
on its own.*

## Limitations & next steps

*Real limitations you found, and concretely how you'd address each one with
more time or data. Not generic hedging.*

## Generative AI use disclosure

*Per the syllabus AI Policy: what you used and how, or "no AI content used."*
