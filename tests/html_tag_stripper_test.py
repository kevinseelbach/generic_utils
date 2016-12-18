from unittest import TestCase

from generic_utils.html_tag_stripper import strip_tags


class TestHTMLTagStripper(TestCase):
    def test_html_tag_strip(self):
        no_html = strip_tags('<DIV class="lia-message-template-question-zone"><H2>Question</H2>')
        self.assertEqual(no_html, "Question")

    def test_remove_script_tag(self):
        no_script = strip_tags('<script language="text/javascript">var foo="bar";</script><div>hello world!</div>')
        self.assertEqual(no_script, 'hello world!')

    def test_remove_cdata_tag(self):
        no_cdata = strip_tags("<title>A Tutorial: <![CDATA[document.write('test');]]></title>")
        self.assertEqual(no_cdata, "A Tutorial: ")

    def test_malformatted_tag(self):
        what = strip_tags("<html><div><p>what is this?</p>")
        self.assertEqual(what, "what is this?")

    def test_nbsp_replaced_by_space(self):
        no_nbsp = strip_tags("<p>Hell&nbsp;o</p>")
        self.assertEqual(no_nbsp, "Hell o")

    def test_real_resource(self):
        real_test = strip_tags('<DIV class="lia-message-template-content-zone"><P>BigPond Broadband sign upTo do this '\
                               'you will need to sign up to broadband:</P>\n<P>&nbsp;</P>\n<P>First you need to '\
                               'create your broadband Cable or ADSL account using the BigPond Broadband sign up:'\
                               '</P>\n<P>&nbsp;</P>\n<UL>\n<LI>On the Customer Details page, answer <STRONG>\'Yes\''\
                               '</STRONG> to the question <STRONG>\'Do you wish to upgrade an existing BigPond Dial '\
                               'Up account?</STRONG>\'.</LI>\n<LI>On the Choose Plan page, under the heading '\
                               '<STRONG>\'What would you like to do with your dial-up account and email address?'\
                               '</STRONG>\', select <STRONG>\'I want to keep my existing email address, and close my '\
                               'existing dial-up account\'</STRONG>.</LI>\n</UL>\n<P><STRONG>Email</STRONG></P>\n<P>'\
                               'You\'ll be able to keep using your existing dial-up email address, so you won\'t need '\
                               'to change any settings in your email program.</P>\n<P>&nbsp;</P>\n'\
                               '<P><STRONG>Dial-up access for three more months</STRONG></P>\n<P>While you\'re '\
                               'getting used to broadband, you\'ll receive three months of unlimited dial-up access '\
                               'at no charge (except for call connection costs). After three months, you\'ll no '\
                               'longer be able to access your dial-up account.</P>\n<P>&nbsp;</P>\n<P><STRONG>'\
                               'Additional Services</STRONG></P>\n<P>If you had any of our Additional '\
                               'Services activated on your dial-up account (except for Global Roaming or BigPond '\
                               'via Telstra Wireless Hotspots), these will remain active and will be billed to your '\
                               'dial-up account unless you choose to cancel them. You can still use your dial-up '\
                               'account for things like your BigPond Music subscription if you wish.</P>\n<P>&nbsp'\
                               ';</P>\n<P>Otherwise, log in with your broadband username and password to activate '\
                               'Additional Services on your new account, view your usage '\
                               'information and manage your boadband plan and account details.</P></DIV>')
        self.assertEqual(real_test, "BigPond Broadband sign upTo do this you will need to sign up to broadband: "\
                                    "First you need to create your broadband Cable or ADSL account using the "\
                                    "BigPond Broadband sign up: On the Customer Details page, answer 'Yes' "\
                                    "to the question 'Do you wish to upgrade an existing BigPond Dial Up account?'."\
                                    "On the Choose Plan page, under the heading 'What would you like to do with "\
                                    "your dial-up account and email address?', select 'I want to keep my existing "\
                                    "email address, and close my existing dial-up account'.EmailYou'll be "\
                                    "able to keep using your existing dial-up email address, so you won't need to "\
                                    "change any settings in your email program. Dial-up access for three more "\
                                    "monthsWhile you're getting used to broadband, you'll receive three months of "\
                                    "unlimited dial-up access at no charge (except for call connection costs). "\
                                    "After three months, you'll no longer be able to access your dial-up account. "\
                                    "Additional ServicesIf you had any of our Additional Services activated on "\
                                    "your dial-up account (except for Global Roaming or BigPond via Telstra "\
                                    "Wireless Hotspots), these will remain active and will be billed to your "\
                                    "dial-up account unless you choose to cancel them. You can still use your "\
                                    "dial-up account for things like your BigPond Music subscription if you "\
                                    "wish. Otherwise, log in with your broadband username and password to "\
                                    "activate Additional Services on your new account, view your usage "\
                                    "information and manage your boadband plan and account details.")
