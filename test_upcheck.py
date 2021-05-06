import unittest
import upcheck
import sys

good_site = {
                "name":"www.google.com",
                "url":"www.google.com",
                "paths":["/search","/","news"],
                "ports":["80","443"]
            }
good_sites = [
            {
                "name":"www.google.com",
                "url":"www.google.com",
                "paths":["/search"]
            },
            {
                "name":"www.reddit.com",
                "url":"www.reddit.com",
                "ports":["80","443"]
            },
        ]
bad_sites = [
            {
                "name":"www.google.comm",
                "url":"www.google.comm",
                "paths":["/search"]
            },
            {
                "name":"www.reddit.comm",
                "url":"www.reddit.comm",
                "ports":["80","443"]
            },            
        ]

class POC_TestCase(unittest.TestCase):
    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

class Basic(unittest.TestCase):
    def test_timestamp(self):
        res = upcheck.timestamp()
        print("Testing timestamp: "+res)
        self.assertIsInstance(res,str)
    
    def test_format_url(self):
        url = upcheck.format_url("www.google.com","https","80")
        print("Testing URL: "+url)


class Sites(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # cls.site_list = upcheck.load_sites()
        cls.good_sites = good_sites
        cls.bad_sites = bad_sites

    @classmethod
    def tearDownClass(cls):
        cls.site_list = None

    def test_load_sites(self):
        sites = upcheck.load_sites("sites.json")
        for site in sites:
            self.assertIsInstance("test",type(""))

    def test_checkSites(self):
        print("Checking good sites:")
        for site in self.good_sites:
            print("Checking site: "+site['name'])
            res = upcheck.check_site(site=site,retries=1)
            self.assertIsNone(res)
        print("Checking bad sites:")
        for site in self.bad_sites:
            print("Checking site: "+site['name'])
            res = upcheck.check_site(site=site,retries=1)
            self.assertIsNotNone(res)

class Alerts(unittest.TestCase):
    def test_send_alert(self):
        upcheck.send_alert("Test Message","Test_Message")

class Paths(unittest.TestCase):
    def test_paths(self):
        paths = upcheck.get_all_paths(good_site)
        print(paths)

class Full(unittest.TestCase):
    def test_monitor(self):
        print(">>> Testing good sites <<<")
        upcheck.monitor(site_list = good_sites)
        print(">>> Testing bad sites <<<")
        upcheck.monitor(site_list = bad_sites, interval=30,email=True)

def run_selected_tests():
    suite = unittest.TestSuite()
    suite.addTest(POC_TestCase('test_upper'))
    return suite

if __name__ == '__main__':
    unittest.main(Full())
    #run suite
    # runner = unittest.TextTestRunner()
    # runner.run(run_selected_tests())