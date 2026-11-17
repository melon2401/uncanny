import hashlib
import unittest
from detector.prepare_slop import prepare


def fixture():
    records=[]
    for split in ("train","validation","test"):
        for platform in ("instagram","tiktok"):
            for label in ("real","ai"):
                for i in range(5):
                    name=f"{split}/{platform}/{label}/{i}.mp4"
                    records.append(dict(file_name=name,split=split,platform=platform,label=label,
                                        creator_id=f"{split}-{platform}-{label}",handle=f"{split}-{label}",
                                        provenance="original",size_bytes="100",sha256=hashlib.sha256(name.encode()).hexdigest()))
    return records


class SlopSelectionTests(unittest.TestCase):
    def test_deterministic_balanced_creator_cap(self):
        result=prepare(fixture())
        self.assertEqual(result,prepare(list(reversed(fixture()))))
        self.assertEqual(result["summary"]["selected_entries"],36)
        self.assertTrue(all(n==3 for n in result["summary"]["counts"].values()))

    def test_excludes_unknown_creators_and_replacement_accounts(self):
        records=fixture()
        records[0]["handle"]=""
        records[1]["provenance"]="cross_account_substitute"
        r=prepare(records)
        self.assertEqual(r["summary"]["exclusions"],dict(unverifiable_creator=1,substitute_provenance=1))

    def test_rejects_creator_leakage_and_identical_content(self):
        records=fixture()
        held=next(r for r in records if r["split"]=="test")
        held["creator_id"]=records[0]["creator_id"]
        with self.assertRaisesRegex(ValueError,"Creator crosses"):
            prepare(records)
        records=fixture()
        next(r for r in records if r["split"]=="test")["sha256"]=records[0]["sha256"]
        with self.assertRaisesRegex(ValueError,"Identical video crosses"):
            prepare(records)

    def test_refuses_wrong_label_path(self):
        records=fixture()
        records[0]["file_name"]="train/instagram/ai/wrong.mp4"
        with self.assertRaisesRegex(ValueError,"path does not match"):
            prepare(records)


if __name__=="__main__":
    unittest.main()
