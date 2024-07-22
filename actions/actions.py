import os
import re
from oauth2client.service_account import ServiceAccountCredentials
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.cloud import storage
import pathlib
import textwrap
import logging
import google.generativeai as genai
import mysql.connector
from mysql.connector import Error

logger = logging.getLogger(__name__)

class StoreServiceAction(Action):

    def name(self) -> Text:
        return "action_store_service"

    @staticmethod
    def slot_mappings(self) -> Dict[Text, Any]:
        return {"service": self.from_text()}
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_message = tracker.latest_message.get('text')
        current_service = tracker.get_slot('service')

        if not current_service:
            return [SlotSet("service", user_message)]
        return []
    
class ActionServiceQuery(Action):
    def name(self) -> str:
        return "action_ask_service_query"

    def format_response(self, response):
        response = re.sub(r'\*\*(.*?)\*\*', r'\033[4m\1\033[0m', response)
        response = response.replace("* ", "\n* ")
        response = re.sub(r'(?<!\n)\n(?!\n)', r'\n\n', response)
        return response

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        name = tracker.get_slot("name")
        email = tracker.get_slot("email")
        phone = tracker.get_slot("phone")
        service = tracker.get_slot("service")

        try:
            connection = mysql.connector.connect(
                user='root',
                password='Mortgage12@##',
                host='localhost',
                database='mortgage_data',
                port=3306
            )
            cursor = connection.cursor(dictionary=True)

            query = ("SELECT * FROM user_data WHERE (name = %s AND email = %s) OR (name = %s AND phone = %s) OR (email = %s AND phone = %s);")
            cursor.execute(query, (name, email, name, phone, email, phone))
            result = cursor.fetchall()

            if result:
                response = self.get_response_from_openai_user_exists(service)
                dispatcher.utter_message(text="You have already submitted your details.\n\n" + response)
            else:
                response = self.get_response_from_openai(service)
                dispatcher.utter_message(text=response)

        except mysql.connector.Error as e:
            dispatcher.utter_message(text=f"Error checking or saving user data in the database: {e}")

        finally:
            if connection.is_connected():
                # Ensure that all results are read before closing the cursor and connection
                cursor.fetchall()
                cursor.close()
                connection.close()

    def get_response_from_openai(self, query):
        try:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bionic-slate-419807-2020a12cd584.json"
            credentials = service_account.Credentials.from_service_account_file("bionic-slate-419807-2020a12cd584.json")
            scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/cloud-platform'])
            storage_client = storage.Client(credentials=scoped_credentials)
            os.environ['GOOGLE_API_KEY'] = "AIzaSyD8K4E0z6EEuzfcsoq8jTqXhXDXWimMUNM"  # Make sure to replace with your actual API key
            genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

            model = genai.GenerativeModel('gemini-1.0-pro-001')

            data = """
            We help you with Swift and Simple Mortgage Solutions. Your Financing, Simplified.
            Join Our Extended Family of 100,000+ Satisfied Customers Who've Saved Big on Mortgage Expenses with Our Custom Plans and Enjoy Lightning-Fast Approvals – No More Bank Hopping for the Perfect Rate.
            Get Quick Approval
            —Please choose an option—First Time Home BuyerMortgage Renewal or TransferMortgage RefinancingConstruction MortgageCommercial MortgagePrivate MortgageTruck LoanInvestment PropertiesHome Equity Line of Credit
            —Please choose an option—
            Our Trusted Lenders
            We work with all the major banks and credit unions in Canada. By using multiple lenders, we increase our chances of getting a good rate and product.

            Our Awards & Achievements

            Hall Of Fame and Diamond Awards From DLC
            A Proud Moment! Here’s Vikramjit Sran, President, Sandhu & Sran Mortgages, receiving the Hall of Fame and Diamond Award 2023 for being the best in the industry from Dominion Lending Centres.

            Apply Now to Secure Exclusive Savings on Processing Fees!
            01
            HRS
            :
            54
            MINS
            :
            03
            SECS
            Act Now! Limited Time Offer: Enjoy a Processing Fee WAIVER on Select Products – Don’t Miss Out on This Opportunity!
            *Terms and conditions apply
            Apply Now
            Mortgage Rates

            Below are our best variable and fixed rates available from Sandhu and Sran Mortgages. We have access to over 40 lenders, and so my available mortgage rates and products are vast. This allows us to match your needs with the right lender and right mortgage product.

            Contact us today for advice on what mortgage rate, lender, and terms fit your needs best.
            Grab Your Rates
            Term (Fixed) Interest Rates*
            1 Year Fixed 6.74%
            2 Year Fixed 6.09%
            3 Year Fixed 4.99%
            4 Year Fixed 5.14%
            5 Year Fixed 4.99%
            7 Year Fixed 5.70%
            10 Year Fixed 6.10%
            MORTGAGE + PROGRAM RATES * March 28th 2024
            What Our Clients Are Saying
            Lovepreet Singh Marahar
            3 months ago
            I couldn’t be happier with the service I received from Vikram Sran. He took the time to understand my financial situation and goals, and then worked tirelessly to find a mortgage solution that was tailored to my needs. I highly recommend them to anyone in need of mortgage assistance.
            N S
            4 years ago
            I have dealt with other mortgage brokers in the past and have not had the best experience. From them prolonging the completion date to not disclosing all information and promising false rates, I decided to try this firm out as I was buying a new property. I have to say from start to finish Ishwinder was on top of it, he went above and beyond to get me the best rate in a short time frame. He always kept me updated of what was going on, as I haven’t had this experience before with other brokers I was absolutely stunned at his professionalism and dedication! There is no question what the advertise is what they deliver. He went over options with me gave me his advice on what he thought would be most beneficial to me. Absolutely the best In the game!!! I will be referring all my friends and family to him in the future! It is hard to find a dedicated honest and reliable broker these days but I am glad I found him finally! Thank you again Ishwinder for all you did for me!
            Yaad Sangha
            4 years ago
            One thing very clear they are very honest and helpful every time thanks sandhu & sran
            justin williams
            4 years ago
            Vikram and Sran are the best. 5 star customer service. 5 star customer experience. Helpful at every turn I had a great experience dealing with Vikram. Definitely recommend to anyone in need of a mortgage broker. Thanks again guys!
            Jeeta Dhillon
            4 years ago
            Sandhu and Sran have very amazing service and very knowledgeable. it was really easy working with you guys.
            Sukhraj Sandhu
            4 years ago
            Sandhu and Sran mortgages are the best mortgage brokers in Abbotsford. They do truck loans and everything and I would recommend going here. They have great service and are very respectful and I hope to see them again soon
            Tara Nand
            4 years ago
            Awesome service. He met us off hours to accommodate us. He made transactions effortless and stress free. Highly recommend! Thank you.
            Armann Otal
            5 years ago
            Ishwinder is a very nice and knowledgeable man. I had a great experience. They treated me with care and I can honestly say I would’ve given them 6 stars. If you ever need a mortgage make sure to come to Sandhu and ran Mortgages. I will definitely be back even for no reason. Outstanding. Like
            Gromvir Dhillon
            5 years ago
            great service and very nice people who care about your money and where it goes. Overall was a very easy process and I highly recommend them for anyone who needs their services.
            Sushil Kumar
            6 years ago
            Excellent Mortgage specialists in Abbotsford, It was very difficult for me to get a mortgage just after switching to a new job, but Mr. Vikram from Sandhu and Sran Mortgages helped me to get the mortgage with in a week. Highly recommended to anyone who need mortgage for homes.
            Apply Now to Secure Your Opportunity Before It’s Gone.

            Apply Now
            Our Featured Products
            We know mortgages, inside and out. If it's a mortgage or anything mortgage related that you need, then you're at the right place. Our mortgage specialists can find the perfect mortgage for you, and always at an unbeatable rate!

            First Time Home Buyer
            Get off on the right foot in your home buying journey with an experienced first time home buyers mortgage broker

            Renewal or Transfer
            When it comes time to renew your mortgage, I'll help you review your options and make the renewal process simple and easy.

            Mortgage Refinancing
            Sometimes, refinancing is your best option for a variety of reasons. Take advantage of your home equity today with mortgage refinancing.

            Construction Mortgage
            If you are thinking of renovating or building a new property, our mortgage consultants are here to provide you flexible construction mortgage options.

            Commercial Mortgage
            We partner with commercial banks and lenders who offer a variety of flexible and creative product options.

            Private Mortgage
            If your financial situation requires a short term, out-of-the-box solution, ask us about our private lending options.

            Investment Properties
            If you're considering an investment in real estate, start by having a conversation with us, to explore some of the innovative new options and great rates available today.

            Line of Credit
            Use the equity in your home to get a secured line of credit today! If you are interested in the HELOC, our mortgage consultants are here to provide you flexible options.

            Truck Loan
            Securing truck loans is not easy but we makes it simpler just for you. We have all the right solutions to guide you through your truck loans.
            Get Your Mortgage Approved With A Low Credit Score!
            0% Down Payment & Lowest Possible Rates Available
            Are banks refusing you a mortgage due to low credit score? Don’t worry, Sandhu & Sran Mortgages is here to get you approved for a mortgage even with a low credit score and at the lowest rate possible, all based on your profile and credit scenario.
            Our private mortgage deals are quite secure and come with no minimal credit score restrictions. If you are having trouble with cash flow, you can avail a mortgage at 0% down payment. Our mortgage deals can help you stay up with your payments and comes with flexible repayment options.
            If you are looking for a private mortgage lender in B.C. who meets all your mortgage needs despite bad credit, we are the ones you can rely on.
            Get started with your mortgage application now.
            Apply Now
            Get Your Construction Mortgage Approved With Us!
            Mortgage Financing For New Builds Available
            Planning to build a property from scratch? Want to renovate the property you already own? If yes, we have got you covered with our construction mortgage deals that meet your budget and expectations. No matter, you are looking for fixed or variable-rate mortgage option, our construction mortgage lenders in B.C. provide a myriad of deals to choose from.
            At Sandhu & Sran Mortgages, we specialize at progress draw mortgage that draws money in phases throughout the building process and you just need to pay interest on the amount borrowed until the construction is completed. Compared to short-term construction mortgage at higher interest rates provided by other brokers, we offer lowest possible interest rates with easy approval.
            File An Online Loan Application Today.
            Apply Now
            See What Sets Us Apart

            Mortgage Expertise You Can Trust
            Our team of licensed, experienced, and independent mortgage brokers brings unparalleled expertise to the table. We provide you with expert advice, guiding you through the complex world of financial options.
            No Hidden Costs - It's on Us
            Your financial goals matter to us. That's why we offer our expert services at no extra cost to you. We swiftly narrow down the list of lenders that align with your unique needs, making your mortgage process fast, easy, and budget-friendly.
            Competitive Rates, Your Way
            We do the legwork for you. Our dedicated team shops the mortgage lenders to secure the best rates available. With us, you gain access to a wide network of banks and lenders competing for your business, ensuring you get the competitive edge you deserve.
            Your Mortgage, Your Trust
            When you choose Sandhu & Sran Mortgages, you're choosing a partner dedicated to your financial success. We don't just know mortgages; we understand your dreams and aspirations. Experience the difference of working with a team committed to making your mortgage journey a seamless one. Trust us to lead you to a brighter financial future.
            Benefits of Applying With Us
            Customized Solutions
            We tailor mortgage products and services to match your unique financial goals and needs.
            Time and Cost Savings
            We streamline the mortgage process, saving you valuable time and eliminating hidden fees. Our services come at no extra cost to you.
            Access to Multiple Lenders
            Gain access to a wide network of lenders, ensuring you receive competitive rates and terms.
            Trust and Transparency
            We prioritize trust and transparency in every transaction, keeping you informed at every step of the process.
            Fast Approvals
            Benefit from our efficient processes that lead to quick mortgage approvals.
            Financial Empowerment
            We empower you to make informed decisions, giving you confidence in your mortgage choices.
            Customer-Centric Approach
            Your satisfaction is our priority. We take a customer-centric approach to ensure your needs are met.
            Tailored Solutions for Low Credit Scores
            Even if you have a low credit score, we have custom mortgage plans designed especially for you.

            Abbotsford Address
            2328 Clearbrook Rd
            Abbotsford, BC V2T 2X5
            Surrey Address
            #108- 7511 120
            Street Delta BC V4C 0C1
            © Copyright 2024 Sandhu and Sran Mortgages.
            """

            prompt = f"""
            Below is the website data of a mortgage company. Please elaborate on FAQ answers to encourage the user to use our mortgage services. Provide relevant responses to user queries as needed using the data below.

            And, here's the company's website data:
            {data}

            User's query: {query}

            If the above service is available with the company by taking into consideration the website content, then start with: Yes, we provide the XYZ service and then explain about the service provided, making the customer satisfactory.
            But, if the query is not related to the service then don't start with 'Yes'. Answer that chunk accordingly and if the user's query is not understandable then introduce Sandhu and Sran Mortgages, and explain about the services provided by them using the website's content.
            """

            response = model.generate_content(prompt)
            formatted_response = self.format_response(response.text)
            return formatted_response

        except Exception as e:
            return f"An error occurred while generating the response: {str(e)}"
    
    
   
    def get_response_from_openai_user_exists(self, query):
        try:
            oos.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bionic-slate-419807-2020a12cd584.json"
            credentials = service_account.Credentials.from_service_account_file("bionic-slate-419807-2020a12cd584.json")
            scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/cloud-platform'])
            storage_client = storage.Client(credentials=scoped_credentials)
            os.environ['GOOGLE_API_KEY'] = "AIzaSyD8K4E0z6EEuzfcsoq8jTqXhXDXWimMUNM"  # Make sure to replace with your actual API key
            genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

            model = genai.GenerativeModel('gemini-1.0-pro-001')

            data = """
            We help you with Swift and Simple Mortgage Solutions. Your Financing, Simplified.
            Join Our Extended Family of 100,000+ Satisfied Customers Who've Saved Big on Mortgage Expenses with Our Custom Plans and Enjoy Lightning-Fast Approvals – No More Bank Hopping for the Perfect Rate.
            Get Quick Approval
            —Please choose an option—First Time Home BuyerMortgage Renewal or TransferMortgage RefinancingConstruction MortgageCommercial MortgagePrivate MortgageTruck LoanInvestment PropertiesHome Equity Line of Credit
            —Please choose an option—
            Our Trusted Lenders
            We work with all the major banks and credit unions in Canada. By using multiple lenders, we increase our chances of getting a good rate and product.

            Our Awards & Achievements

            Hall Of Fame and Diamond Awards From DLC
            A Proud Moment! Here’s Vikramjit Sran, President, Sandhu & Sran Mortgages, receiving the Hall of Fame and Diamond Award 2023 for being the best in the industry from Dominion Lending Centres.

            Apply Now to Secure Exclusive Savings on Processing Fees!
            01
            HRS
            :
            54
            MINS
            :
            03
            SECS
            Act Now! Limited Time Offer: Enjoy a Processing Fee WAIVER on Select Products – Don’t Miss Out on This Opportunity!
            *Terms and conditions apply
            Apply Now
            Mortgage Rates

            Below are our best variable and fixed rates available from Sandhu and Sran Mortgages. We have access to over 40 lenders, and so my available mortgage rates and products are vast. This allows us to match your needs with the right lender and right mortgage product.

            Contact us today for advice on what mortgage rate, lender, and terms fit your needs best.
            Grab Your Rates
            Term (Fixed) Interest Rates*
            1 Year Fixed 6.74%
            2 Year Fixed 6.09%
            3 Year Fixed 4.99%
            4 Year Fixed 5.14%
            5 Year Fixed 4.99%
            7 Year Fixed 5.70%
            10 Year Fixed 6.10%
            MORTGAGE + PROGRAM RATES * March 28th 2024
            What Our Clients Are Saying
            Lovepreet Singh Marahar
            3 months ago
            I couldn’t be happier with the service I received from Vikram Sran. He took the time to understand my financial situation and goals, and then worked tirelessly to find a mortgage solution that was tailored to my needs. I highly recommend them to anyone in need of mortgage assistance.
            N S
            4 years ago
            I have dealt with other mortgage brokers in the past and have not had the best experience. From them prolonging the completion date to not disclosing all information and promising false rates, I decided to try this firm out as I was buying a new property. I have to say from start to finish Ishwinder was on top of it, he went above and beyond to get me the best rate in a short time frame. He always kept me updated of what was going on, as I haven’t had this experience before with other brokers I was absolutely stunned at his professionalism and dedication! There is no question what the advertise is what they deliver. He went over options with me gave me his advice on what he thought would be most beneficial to me. Absolutely the best In the game!!! I will be referring all my friends and family to him in the future! It is hard to find a dedicated honest and reliable broker these days but I am glad I found him finally! Thank you again Ishwinder for all you did for me!
            Yaad Sangha
            4 years ago
            One thing very clear they are very honest and helpful every time thanks sandhu & sran
            justin williams
            4 years ago
            Vikram and Sran are the best. 5 star customer service. 5 star customer experience. Helpful at every turn I had a great experience dealing with Vikram. Definitely recommend to anyone in need of a mortgage broker. Thanks again guys!
            Jeeta Dhillon
            4 years ago
            Sandhu and Sran have very amazing service and very knowledgeable. it was really easy working with you guys.
            Sukhraj Sandhu
            4 years ago
            Sandhu and Sran mortgages are the best mortgage brokers in Abbotsford. They do truck loans and everything and I would recommend going here. They have great service and are very respectful and I hope to see them again soon
            Tara Nand
            4 years ago
            Awesome service. He met us off hours to accommodate us. He made transactions effortless and stress free. Highly recommend! Thank you.
            Armann Otal
            5 years ago
            Ishwinder is a very nice and knowledgeable man. I had a great experience. They treated me with care and I can honestly say I would’ve given them 6 stars. If you ever need a mortgage make sure to come to Sandhu and ran Mortgages. I will definitely be back even for no reason. Outstanding. Like
            Gromvir Dhillon
            5 years ago
            great service and very nice people who care about your money and where it goes. Overall was a very easy process and I highly recommend them for anyone who needs their services.
            Sushil Kumar
            6 years ago
            Excellent Mortgage specialists in Abbotsford, It was very difficult for me to get a mortgage just after switching to a new job, but Mr. Vikram from Sandhu and Sran Mortgages helped me to get the mortgage with in a week. Highly recommended to anyone who need mortgage for homes.
            Apply Now to Secure Your Opportunity Before It’s Gone.

            Apply Now
            Our Featured Products
            We know mortgages, inside and out. If it's a mortgage or anything mortgage related that you need, then you're at the right place. Our mortgage specialists can find the perfect mortgage for you, and always at an unbeatable rate!

            First Time Home Buyer
            Get off on the right foot in your home buying journey with an experienced first time home buyers mortgage broker

            Renewal or Transfer
            When it comes time to renew your mortgage, I'll help you review your options and make the renewal process simple and easy.

            Mortgage Refinancing
            Sometimes, refinancing is your best option for a variety of reasons. Take advantage of your home equity today with mortgage refinancing.

            Construction Mortgage
            If you are thinking of renovating or building a new property, our mortgage consultants are here to provide you flexible construction mortgage options.

            Commercial Mortgage
            We partner with commercial banks and lenders who offer a variety of flexible and creative product options.

            Private Mortgage
            If your financial situation requires a short term, out-of-the-box solution, ask us about our private lending options.

            Investment Properties
            If you're considering an investment in real estate, start by having a conversation with us, to explore some of the innovative new options and great rates available today.

            Line of Credit
            Use the equity in your home to get a secured line of credit today! If you are interested in the HELOC, our mortgage consultants are here to provide you flexible options.

            Truck Loan
            Securing truck loans is not easy but we makes it simpler just for you. We have all the right solutions to guide you through your truck loans.
            Get Your Mortgage Approved With A Low Credit Score!
            0% Down Payment & Lowest Possible Rates Available
            Are banks refusing you a mortgage due to low credit score? Don’t worry, Sandhu & Sran Mortgages is here to get you approved for a mortgage even with a low credit score and at the lowest rate possible, all based on your profile and credit scenario.
            Our private mortgage deals are quite secure and come with no minimal credit score restrictions. If you are having trouble with cash flow, you can avail a mortgage at 0% down payment. Our mortgage deals can help you stay up with your payments and comes with flexible repayment options.
            If you are looking for a private mortgage lender in B.C. who meets all your mortgage needs despite bad credit, we are the ones you can rely on.
            Get started with your mortgage application now.
            Apply Now
            Get Your Construction Mortgage Approved With Us!
            Mortgage Financing For New Builds Available
            Planning to build a property from scratch? Want to renovate the property you already own? If yes, we have got you covered with our construction mortgage deals that meet your budget and expectations. No matter, you are looking for fixed or variable-rate mortgage option, our construction mortgage lenders in B.C. provide a myriad of deals to choose from.
            At Sandhu & Sran Mortgages, we specialize at progress draw mortgage that draws money in phases throughout the building process and you just need to pay interest on the amount borrowed until the construction is completed. Compared to short-term construction mortgage at higher interest rates provided by other brokers, we offer lowest possible interest rates with easy approval.
            File An Online Loan Application Today.
            Apply Now
            See What Sets Us Apart

            Mortgage Expertise You Can Trust
            Our team of licensed, experienced, and independent mortgage brokers brings unparalleled expertise to the table. We provide you with expert advice, guiding you through the complex world of financial options.
            No Hidden Costs - It's on Us
            Your financial goals matter to us. That's why we offer our expert services at no extra cost to you. We swiftly narrow down the list of lenders that align with your unique needs, making your mortgage process fast, easy, and budget-friendly.
            Competitive Rates, Your Way
            We do the legwork for you. Our dedicated team shops the mortgage lenders to secure the best rates available. With us, you gain access to a wide network of banks and lenders competing for your business, ensuring you get the competitive edge you deserve.
            Your Mortgage, Your Trust
            When you choose Sandhu & Sran Mortgages, you're choosing a partner dedicated to your financial success. We don't just know mortgages; we understand your dreams and aspirations. Experience the difference of working with a team committed to making your mortgage journey a seamless one. Trust us to lead you to a brighter financial future.
            Benefits of Applying With Us
            Customized Solutions
            We tailor mortgage products and services to match your unique financial goals and needs.
            Time and Cost Savings
            We streamline the mortgage process, saving you valuable time and eliminating hidden fees. Our services come at no extra cost to you.
            Access to Multiple Lenders
            Gain access to a wide network of lenders, ensuring you receive competitive rates and terms.
            Trust and Transparency
            We prioritize trust and transparency in every transaction, keeping you informed at every step of the process.
            Fast Approvals
            Benefit from our efficient processes that lead to quick mortgage approvals.
            Financial Empowerment
            We empower you to make informed decisions, giving you confidence in your mortgage choices.
            Customer-Centric Approach
            Your satisfaction is our priority. We take a customer-centric approach to ensure your needs are met.
            Tailored Solutions for Low Credit Scores
            Even if you have a low credit score, we have custom mortgage plans designed especially for you.

            Abbotsford Address
            2328 Clearbrook Rd
            Abbotsford, BC V2T 2X5
            Surrey Address
            #108- 7511 120
            Street Delta BC V4C 0C1
            © Copyright 2024 Sandhu and Sran Mortgages.
            """

            prompt = f"""
            Below is the website data of a mortgage company. Please elaborate on FAQ answers to encourage the user to use our mortgage services. Provide relevant responses to user queries as needed using the data below.

            And, here's the company's website data:
            {data}

            User's query: {query}

            Reply to this query questiion in a way answering the user that already exists. But, if the query is not related to service then don't start with 'Yes'. nswer that chunk accordingly and if the user's query is not understandable then explain about the services provided by Sandhu and Sran Mortgages using the website's content.
            """

            response = model.generate_content(prompt)
            formatted_response = self.format_response(response.text)
            return formatted_response

        except Exception as e:
            return f"An error occurred while generating the response: {str(e)}"


class ActionStoreData(Action):
    def name(self) -> str:
        return "action_store"

    def format_response(self, response):
        response = re.sub(r'\*\*(.*?)\*\*', r'\033[4m\1\033[0m', response)

        # Ensure text with a single asterisk starts on a new line
        response = response.replace("* ", "\n* ")

        # Insert a blank line after each paragraph
        response = re.sub(r'(?<!\n)\n(?!\n)', r'\n\n', response)
        return response

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        # Extract slot values
        name = tracker.get_slot("name")
        email = tracker.get_slot("email")
        phone = tracker.get_slot("phone")
        mortgage_type = tracker.get_slot("mortgage_type")
        service = tracker.get_slot("service")

        try:
            # Connect to the database
            connection = mysql.connector.connect(
                user='root',
                password='Mortgage12@##',
                host='localhost',
                database='mortgage_data',
                port=3306
            )
            cursor = connection.cursor(dictionary=True)

            # Check if the user already exists
            query = (
                "SELECT * FROM user_data "
                "WHERE (name = %s AND email = %s) OR (name = %s AND phone = %s) OR (email = %s AND phone = %s);"
            )
            cursor.execute(query, (name, email, name, phone, email, phone))
            result = cursor.fetchall()

            if result:
                return []
                
            else:
                # Insert new user data if user does not exist
                add_slot = (
                    "INSERT INTO user_data (name, email, phone, service, mortgage_type) "
                    "VALUES (%s, %s, %s, %s, %s);"
                )
                data_slot = (name, email, phone, service, mortgage_type)
                cursor.execute(add_slot, data_slot)
                connection.commit()
                dispatcher.utter_message(text="Slot values saved to the database!")
                return []

        except mysql.connector.Error as e:
            dispatcher.utter_message(text=f"Error checking or saving user data in the database: {e}")
            return []

        finally:
            if connection.is_connected():
                # Ensure that all results are read before closing the cursor and connection
                cursor.fetchall()
                cursor.close()
                connection.close()   


class ActionAnswerMortgageQuestion(Action):

	def name(self) -> Text:
		return "action_ask_query_"
	
	def format_response(self, response):
		response = re.sub(r'\*\*(.*?)\*\*', r'\033[4m\1\033[0m', response)

		# Ensure text with a single asterisk starts on a new line
		response = response.replace("* ", "\n* ")
		
		# Insert a blank line after each paragraph
		response = re.sub(r'(?<!\n)\n(?!\n)', r'\n\n', response)
		return response
	
	def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
		user_message = tracker.latest_message.get('text')
		response = self.get_response_from_openai(user_message)
		dispatcher.utter_message(text=response)
		return []

	def get_response_from_openai(self, query):
		try:
			os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "bionic-slate-419807-2020a12cd584.json"
			credentials = service_account.Credentials.from_service_account_file("bionic-slate-419807-2020a12cd584.json")
			scoped_credentials = credentials.with_scopes(['https://www.googleapis.com/auth/cloud-platform'])
			storage_client = storage.Client(credentials=scoped_credentials)
			os.environ['GOOGLE_API_KEY'] = "AIzaSyD8K4E0z6EEuzfcsoq8jTqXhXDXWimMUNM"  # Make sure to replace with your actual API key
			genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

			model = genai.GenerativeModel('gemini-1.0-pro-001')

			# Predefined FAQs
			predefined_answers = """
			Frequently Asked Questions (FAQs):

			1. What types of mortgages are available in Canada?
			   Answer: There are several types of mortgages available in Canada, including fixed-rate mortgages, variable-rate mortgages, and adjustable-rate mortgages.

			2. What is the current interest rate for mortgages in Canada?
			   Answer: Interest rates for mortgages in Canada can vary widely depending on the lender, the type of mortgage, and the borrower's credit score. The current overnight rate by Bank of Canada is 4.75%. It is best to contact a mortgage broker to get the most up-to-date information on interest rates.

			3. What is the minimum down payment required for a mortgage?
			   Answer: The minimum down payment required for a mortgage in Canada is typically 5% of the purchase price for homes under $500,000. For homes over $500,000, the minimum down payment is 5% of the first $500,000 and 10% of the remaining balance.

			4. What is mortgage pre-approval and how does it work?
			   Answer: Mortgage pre-approval is a process in which a lender determines how much money they are willing to lend you based on your financial information. This can help you determine your budget when shopping for a home.

			5. What documents do I need to apply for a mortgage?
			   Answer: To apply for a mortgage in Canada, you will need to provide documents such as proof of income, proof of employment, bank statements, and identification.

			6. How long does it take to get approved for a mortgage?
			   Answer: The approval process for a mortgage can vary depending on the lender and your financial situation. It can take anywhere from a few days to a few weeks to get approved for a mortgage.

			7. Can I get a mortgage with bad credit in Canada?
			   Answer: It is possible to get a mortgage in Canada with bad credit, but it may be more difficult and you may face higher interest rates. A mortgage broker can help you explore your options.

			8. What fees are associated with getting a mortgage?
			   Answer: There are various fees associated with getting a mortgage in Canada, including appraisal fees, title insurance fees, and legal fees. Your mortgage broker can provide you with a breakdown of all the fees you can expect to pay.

			9. Can I buy a home with a mortgage if I am self-employed?
			   Answer: Yes, it is possible to buy a home with a mortgage if you are self-employed. However, you may need to provide additional documentation to prove your income.

			10. Can I refinance my mortgage?
				Answer: Yes, you can refinance your mortgage in Canada. This can help you lower your interest rate, shorten your loan term, or access the equity in your home.

			11. What is mortgage insurance and do I need it in Canada?
				Answer: Mortgage insurance is typically required if your down payment is less than 20% of the purchase price. This insurance protects the lender in case you default on your mortgage.

			12. Can I pay off my mortgage early?
				Answer: Yes, you can pay off your mortgage early. However, some lenders may charge a prepayment penalty for paying off your mortgage before the end of the term.

			13. Who is a mortgage broker and how can they help me?
				Answer: A mortgage broker is a professional who can help you find the best mortgage product for your financial situation. They can shop around with different lenders to find you the best interest rate and terms.

			14. What is a mortgage prepayment penalty in Canada?
				Answer: A mortgage prepayment penalty is a fee charged by the lender if you pay off your mortgage before the end of the term. This fee can vary depending on the lender and the terms of your mortgage.

			15. Can I get a mortgage if I am a first-time homebuyer in Canada?
				Answer: Yes, first-time homebuyers in Canada can get a mortgage. There are also programs available to help first-time homebuyers, such as the First-Time Home Buyer Incentive.

			16. What is the maximum mortgage amount I can qualify for?
				Answer: The maximum mortgage amount you can qualify for will depend on your income, credit score, and other financial factors. A mortgage broker can help you determine how much you can afford to borrow.

			17. Can I get a mortgage if I am a temporary resident or non-resident?
				Answer: Yes, temporary residents and non-residents can get a mortgage, but they may face additional requirements. It is best to consult with a mortgage broker to discuss your options.

			18. What is a mortgage broker fee?
				Answer: A mortgage broker fee is a fee charged by the mortgage broker for their services. This fee can vary depending on the broker and the complexity of your mortgage application.

			19. What is a mortgage rate hold in Canada?
				Answer: A mortgage rate hold is a guarantee from a lender that they will offer you a specific interest rate for a certain period of time. This can help you secure a rate while you shop for a home.

			20. Can I transfer my mortgage to a new property?
				Answer: Yes, you can transfer your mortgage to a new property. This is known as a portability feature.
			"""

			data="""
			We help you with Swift and Simple Mortgage Solutions. Your Financing, Simplified.
			Join Our Extended Family of 100,000+ Satisfied Customers Who've Saved Big on Mortgage Expenses with Our Custom Plans and Enjoy Lightning-Fast Approvals – No More Bank Hopping for the Perfect Rate.
			Get Quick Approval
			—Please choose an option—First Time Home BuyerMortgage Renewal or TransferMortgage RefinancingConstruction MortgageCommercial MortgagePrivate MortgageTruck LoanInvestment PropertiesHome Equity Line of Credit
			—Please choose an option—
			Our Trusted Lenders
			We work with all the major banks and credit unions in Canada. By using multiple lenders, we increase our chances of getting a good rate and product.
			
			Our Awards & Achievements


			Hall Of Fame and Diamond Awards From DLC
			A Proud Moment! Here’s Vikramjit Sran, President, Sandhu & Sran Mortgages, receiving the Hall of Fame and Diamond Award 2023 for being the best in the industry from Dominion Lending Centres.
			
			Apply Now to Secure Exclusive Savings on Processing Fees!
			01
			HRS
			:
			54
			MINS
			:
			03
			SECS
			Act Now! Limited Time Offer: Enjoy a Processing Fee WAIVER on Select Products – Don’t Miss Out on This Opportunity!
			*Terms and conditions apply
			Apply Now
			Mortgage Rates


			Below are our best variable and fixed rates available from Sandhu and Sran Mortgages. We have access to over 40 lenders, and so my available mortgage rates and products are vast. This allows us to match your needs with the right lender and right mortgage product.

			Contact us today for advice on what mortgage rate, lender, and terms fit your needs best.
			Grab Your Rates
			Term (Fixed)	Interest Rates*
			1 Year Fixed	6.74%
			2 Year Fixed	6.09%
			3 Year Fixed	4.99%
			4 Year Fixed	5.14%
			5 Year Fixed	4.99%
			7 Year Fixed	5.70%
			10 Year Fixed	6.10%
			MORTGAGE + PROGRAM RATES * March 28th 2024
			What Our Clients Are Saying
			Lovepreet Singh Marahar
			3 months ago
			I couldn’t be happier with the service I received from Vikram Sran. He took the time to understand my financial situation and goals, and then worked tirelessly to find a mortgage solution that was tailored to my needs. I highly recommend them to anyone in need of mortgage assistance.”
			N S
			4 years ago
			I have dealt with other mortgage brokers in the past and have not had the best experience. From them prolonging the completion date to not disclosing all information and promising false rates, I decided to try this firm out as I was buying a new property. I have to say from start to finish Ishwinder was on top of it, he went above and beyond to get me the best rate in a short time frame. He always kept me updated of what was going on, as I haven’t had this experience before with other brokers I was absolutely stunned at his professionalism and dedication! There is no question what the advertise is what they deliver. He went over options with me gave me his advice on what he thought would be most beneficial to me. Absolutely the best In the game!!! I will be referring all my friends and family to him in the future! It is hard to find a dedicated honest and reliable broker these days but I am glad I found him finally! Thank you again Ishwinder for all you did for me!
			Yaad Sangha
			4 years ago
			One thing very clear they are very honest and helpful every time thanks sandhu & sran
			justin williams
			4 years ago
			Vikram and Sran are the best. 5 star customer service. 5 star customer experience. Helpful at every turn I had a great experience dealing with Vikram. Definitely recommend to anyone in need of a mortgage broker. Thanks again guys!
			Jeeta Dhillon
			4 years ago
			Sandhu and Sran have very amazing service and very knowledgeable. it was really easy working with you guys.
			Sukhraj Sandhu
			4 years ago
			Sandhu and Sran mortgages are the best mortgage brokers in Abbotsford. They do truck loans and everything and I would recommend going here. They have great service and are very respectful and I hope to see them again soon
			Tara Nand
			4 years ago
			Awesome service. He met us off hours to accommodate us. He made transactions effortless and stress free. Highly recommend! Thank you.
			Armann Otal
			5 years ago
			Ishwinder is a very nice and knowledgeable man. I had a great experience. They treated me with care and I can honestly say I would’ve given them 6 stars. If you ever need a mortgage make sure to come to Sandhu and ran Mortgages. I will definitely be back even for no reason. Outstanding.Like
			Gromvir Dhillon
			5 years ago
			great service and very nice people who care about your money and where it goes. Overall was a very easy process and I highly recommend them for anyone who needs their services.
			Sushil Kumar
			6 years ago
			Excellent Mortgage specialists in Abbotsford, It was very difficult for me to get a mortgage just after switching to a new job, but Mr. Vikram from Sandhu and Sran Mortgages helped me to get the mortgage with in a week. Highly recommended to anyone who need mortgage for homes.
			Apply Now to Secure Your Opportunity Before It’s Gone.

			Apply Now
			Our Featured Products
			We know mortgages, inside and out. If it's a mortgage or anything mortgage related that you need, then you're at the right place. Our mortgage specialists can find the perfect mortgage for you, and always at an unbeatable rate!
			
			First Time Home Buyer
			Get off on the right foot in your home buying journey with an experienced first time home buyers mortgage broker
			
			Renewal or Transfer
			When it comes time to renew your mortgage, I'll help you review your options and make the renewal process simple and easy.
			
			Mortgage Refinancing
			Sometimes, refinancing is your best option for a variety of reasons. Take advantage of your home equity today with mortgage refinancing.
			
			Construction Mortgage
			If you are thinking of renovating or building a new property, our mortgage consultants are here to provide you flexible construction mortgage options.
			
			Commercial Mortgage
			We partner with commercial banks and lenders who offer a variety of flexible and creative product options.
			
			Private Mortgage
			If your financial situation requires a short term, out-of-the-box solution, ask us about our private lending options.
			
			Investment Properties
			If you're considering an investment in real estate, start by having a conversation with us, to explore some of the innovative new options and great rates available today.
			
			Line of Credit
			Use the equity in your home to get a secured line of credit today! If you are interested in the HELOC, our mortgage consultants are here to provide you flexible options.
			
			Truck Loan
			Securing truck loans is not easy but we makes it simpler just for you. We have all the right solutions to guide you through your truck loans.
			Get Your Mortgage Approved With A Low Credit Score!
			0% Down Payment & Lowest Possible Rates Available
			Are banks refusing you a mortgage due to low credit score? Don’t worry, Sandhu & Sran Mortgages is here to get you approved for a mortgage even with a low credit score and at the lowest rate possible, all based on your profile and credit scenario.
			Our private mortgage deals are quite secure and come with no minimal credit score restrictions. If you are having trouble with cash flow, you can avail a mortgage at 0% down payment. Our mortgage deals can help you stay up with your payments and comes with flexible repayment options.
			If you are looking for a private mortgage lender in B.C. who meets all your mortgage needs despite bad credit, we are the ones you can rely on.
			Get started with your mortgage application now.
			Apply Now
			Get Your Construction Mortgage Approved With Us!
			Mortgage Financing For New Builds Available
			Planning to build a property from scratch? Want to renovate the property you already own? If yes, we have got you covered with our construction mortgage deals that meet your budget and expectations. No matter, you are looking for fixed or variable-rate mortgage option, our construction mortgage lenders in B.C. provide a myriad of deals to choose from.
			At Sandhu & Sran Mortgages, we specialize at progress draw mortgage that draws money in phases throughout the building process and you just need to pay interest on the amount borrowed until the construction is completed. Compared to short-term construction mortgage at higher interest rates provided by other brokers, we offer lowest possible interest rates with easy approval.
			File An Online Loan Application Today.
			Apply Now
			See What Sets Us Apart


			Mortgage Expertise You Can Trust
			Our team of licensed, experienced, and independent mortgage brokers brings unparalleled expertise to the table. We provide you with expert advice, guiding you through the complex world of financial options.
			No Hidden Costs - It's on Us
			Your financial goals matter to us. That's why we offer our expert services at no extra cost to you. We swiftly narrow down the list of lenders that align with your unique needs, making your mortgage process fast, easy, and budget-friendly.
			Competitive Rates, Your Way
			We do the legwork for you. Our dedicated team shops the mortgage lenders to secure the best rates available. With us, you gain access to a wide network of banks and lenders competing for your business, ensuring you get the competitive edge you deserve.
			Your Mortgage, Your Trust
			When you choose Sandhu & Sran Mortgages, you're choosing a partner dedicated to your financial success. We don't just know mortgages; we understand your dreams and aspirations. Experience the difference of working with a team committed to making your mortgage journey a seamless one. Trust us to lead you to a brighter financial future.
			Benefits of Applying With Us
			Customized Solutions
			We tailor mortgage products and services to match your unique financial goals and needs.
			Time and Cost Savings
			We streamline the mortgage process, saving you valuable time and eliminating hidden fees. Our services come at no extra cost to you.
			Access to Multiple Lenders
			Gain access to a wide network of lenders, ensuring you receive competitive rates and terms.
			Trust and Transparency
			We prioritize trust and transparency in every transaction, keeping you informed at every step of the process.
			Fast Approvals
			Benefit from our efficient processes that lead to quick mortgage approvals.
			Financial Empowerment
			We empower you to make informed decisions, giving you confidence in your mortgage choices.
			Customer-Centric Approach
			Your satisfaction is our priority. We take a customer-centric approach to ensure your needs are met.
			Tailored Solutions for Low Credit Scores
			Even if you have a low credit score, we have custom mortgage plans designed especially for you.

			Abbotsford Address
			2328 Clearbrook Rd
			Abbotsford, BC V2T 2X5
			Surrey Address
			#108- 7511 120
			Street Delta BC V4C 0C1
			© Copyright 2024 Sandhu and Sran Mortgages.

			
			"""

			prompt = f"""
			Below are some frequently asked questions (FAQs) about mortgages in Canada with their answers, and there's website data. Please elaborate on FAQ answers to encourage the user to use our mortgage services. Provide relevant responses to user queries as needed using the data below.

			FAQs:
			{predefined_answers}

			and, here's the company's website data:
			{data}

			User's query: {query}
			"""

			response = model.generate_content(prompt)
			formatted_response = self.format_response(response.text)
			return formatted_response
		
		except Exception as e:
			return f"Sorry, I couldn't process your request due to an error: {str(e)}"