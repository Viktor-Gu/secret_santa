import smtplib, ssl
from email.message import EmailMessage
import random
from datetime import datetime

from string import Template

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

MY_ADDRESS = ''
PASSWORD = ''
try:
    with open("credentials.txt") as cred_file:
        for credentials in cred_file:
            MY_ADDRESS = credentials.split()[0]
            PASSWORD = credentials.split()[1]
except FileNotFoundError:
    print("ERROR: no credential file! Expecting TXT file with '[email address] [password]'")
    exit(-1)


def get_contacts(filename):
    """
    Return two lists names, emails containing names and email addresses
    read from a file specified by filename.
    """

    names = []
    emails = []
    with open(filename, mode='r', encoding='utf-8') as contacts_file:
        for a_contact in contacts_file:
            names.append(a_contact.split()[0])
            emails.append(a_contact.split()[1])
    return names, emails


def read_template(filename):
    """
    Returns a Template object comprising the contents of the
    file specified by filename.
    """

    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)


def get_exceptions(filename):
    exceptions = list()
    with open(filename, 'r', encoding='utf-8') as exception_file:
        for a_contact in exception_file:
            exceptions.append((a_contact.split()[0], a_contact.split()[1]))
    return exceptions


def write_combinations(wichtel_combinations):
    with open("combinations.txt", "w") as comb_file:
        print(wichtel_combinations, file=comb_file)


def choose_wichtel(names, exceptions):
    # check input
    for n1, n2 in exceptions:
        if n1 not in names or n2 not in names:
            return None

    wichtel_combinations = dict()
    player_dict = dict()
    for name in names:
        player_dict[name] = names.copy()

    # remove own name
    for key, value in player_dict.items():
        if key in value:
            value.remove(key)

    # remove exceptions
    for name1, name2 in exceptions:
        if name1 in player_dict and name2 in player_dict[name1]:
            player_dict[name1].remove(name2)
        if name2 in player_dict and name1 in player_dict[name2]:
            player_dict[name2].remove(name1)

    # check exception validity (might be extended)
    if any(x == [] for key, x in player_dict.items()):
        error_names = [k for k, v in player_dict.items() if v == []]
        for name in error_names:
            print(f"Error: not possible solution for {name}. Reduce Exception list.")
        return None

    for i in range(len(names)):
        # sort names from least length to most length of partners
        sorted_names = sorted(player_dict, key=lambda key: len(player_dict[key]))
        if len(sorted_names) != 0:
            # choose partner for player
            if len(player_dict[sorted_names[0]]) > 0:
                wichtel_combinations[sorted_names[0]] = partner = random.choice(player_dict[sorted_names[0]])

                # delete selected partner from all other participants
                for partner_list in player_dict.values():
                    if partner in partner_list:
                        if len(partner_list) != 1:
                            partner_list.remove(partner)
                        else:
                            if len(player_dict) > 1:
                                print("Possibly not enough drawing possibilities")
                                return None  # muss nicht sein aber zur sicherheit

                # delete player
                del player_dict[sorted_names[0]]
            else:
                print("Error: One participant did not find a match")
                return None

    # check results
    if len(wichtel_combinations) != len(names):
        return None
    if any(value == key for key, value in wichtel_combinations.items()):
        return None
    if not all(name in wichtel_combinations for name in names):
        return None
    if not all(name in wichtel_combinations.values() for name in names):
        return None
    if len(wichtel_combinations) != len(set(wichtel_combinations.values())):
        return None

    return wichtel_combinations


def check_combs(wichtel_combinations):
    for key, value in wichtel_combinations.items():
        if wichtel_combinations[value] == key:
            return False
    return True


def send_mail(message, receiver_email, subject):

    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    password = "16-digit-app-password"

    msg = EmailMessage()
    msg.set_content(message)
    msg['Subject'] = subject
    msg['From'] = MY_ADDRESS
    msg['To'] = receiver_email

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(MY_ADDRESS, PASSWORD)
        server.send_message(msg, from_addr=MY_ADDRESS, to_addrs=receiver_email)


def wichteln():
    # get year
    today = datetime.today()
    year = today.year

    # get params
    names, emails = get_contacts('mycontacts.txt')  # read contacts
    message_template = read_template('message.txt')
    exceptions = get_exceptions('exceptions.txt')

    # choose wichtel
    wichtel_combinations = dict()
    while wichtel_combinations == dict() or wichtel_combinations is None or not check_combs(wichtel_combinations):
        wichtel_combinations = choose_wichtel(names, exceptions)
        # print(wichtel_combinations)

    # Write wichtel combinations to file in case someone forgets
    write_combinations(wichtel_combinations)

    if wichtel_combinations is not None:

        # For each contact, send the email:
        for name, email in zip(names, emails):
            print(f'Sending email to {name} at {email}')

            # add in the actual person name to the message template
            message = message_template.substitute(PERSON_NAME=name.title(),
                                                  WICHTEL_NAME=wichtel_combinations[name.title()])

            # Prints out the message body for our sake
            # print(message)

            send_mail(message, email, "Weihnachts-Wichteln " + str(year))


if __name__ == '__main__':
    wichteln()
