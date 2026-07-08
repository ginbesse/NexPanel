import unittest

import app


class AspNetFlowTests(unittest.TestCase):
    def test_hidden_fields_are_extracted(self):
        html = '''
        <html><body>
        <form>
          <input type="hidden" name="__VIEWSTATE" value="abc123" />
          <input type="hidden" name="__VIEWSTATEGENERATOR" value="gen1" />
          <input type="hidden" name="__EVENTVALIDATION" value="evt456" />
          <input type="text" name="txtKullaniciAdi" value="" />
        </form>
        </body></html>
        '''
        fields = app.parse_hidden_fields(html)
        self.assertEqual(fields["__VIEWSTATE"], "abc123")
        self.assertEqual(fields["__VIEWSTATEGENERATOR"], "gen1")
        self.assertEqual(fields["__EVENTVALIDATION"], "evt456")

    def test_login_fields_are_detected(self):
        html = '''
        <html><body>
        <form>
          <input type="text" name="txtKullaniciAdi" />
          <input type="password" name="txtSifre" />
          <input type="text" name="txtCaptcha" />
          <input type="hidden" name="__VIEWSTATE" value="abc" />
        </form>
        </body></html>
        '''
        fields = app.detect_login_fields(html)
        self.assertEqual(fields["username_field"], "txtKullaniciAdi")
        self.assertEqual(fields["password_field"], "txtSifre")
        self.assertEqual(fields["captcha_field"], "txtCaptcha")


if __name__ == "__main__":
    unittest.main()
