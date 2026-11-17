# Reported known-real false positive

The latest user-labeled real export contains six direct-pixel 720x1280 JPEGs,
advancing from 77.79 to 83.38 seconds. No padding was used. The live model's frame
logits were 6.42, 5.27, 6.32, 0.84, 5.45, -2.98, yielding a positive mean and five
positive signs: 'AI-like visual signal'. Accepting the user's provenance label,
this is a false positive, not a successful result or harmless abstention.

Visual inspection shows a person preparing/drinking beverages. The 504-square
crop removes much of the scene and face. There is a scene change within the clip.
Neither observation establishes causation or synthetic provenance.

A controlled approximation of the old capture path (downsample saved frames to
405x720 with bilinear interpolation, JPEG quality 90, then original preprocessing)
also falsely flagged the sample: all six logits positive, mean 2.79. This does not
exactly reproduce Chrome's original resampling, but shows that changing image size
alone does not eliminate this failure. No threshold was changed to fit the sample.

The prior zero false flags on a small development set did not generalize to this
new example. The model is not validated for reliable authenticity classification.
Keep this failure in future evaluation. Raw media remains in ignored local captures.
