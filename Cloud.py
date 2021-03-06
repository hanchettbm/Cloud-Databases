import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import random

# Connect to Firebase project.
cred = credentials.Certificate("/Volumes/File Storage/School/Spring 2021/CSE 310/CSE 310 Work/Cloud Database/Cloud-Databases/access.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# Validates user or prompts them to set up account.
def validate(user):
    quit = False
    while not quit:
        result = db.collection("Users").document(user).get()
        if result.exists:
            cloud_dict = result.to_dict()
            cloud_pass = cloud_dict.get("password")
            user_password =  input("Enter your password Here: ")
            # Compares user input to cloud stored info here.
            if user_password == cloud_pass:
                print("\n")
                return cloud_dict
            else:
                print ("Incorrect Login Info, Try Again")
        else:
            # Create new user.
            response = input("We have not seen your username before, would you like to create an account (y/n)? ")
            response == response.lower()
            if response == "y":
                new_user = input("Enter your useranme Here: ")
                password = input("Enter your password Here: ")
                user_data = {"password" : password}
                # Adds password to databse. 
                db.collection("Users").document(new_user).set(user_data)
                result = db.collection("Users").document(user).get()
                if result.exists:
                    # Once added check again. 
                    cloud_dict = result.to_dict()
                    cloud_pass = cloud_dict.get("password")
                    user_password =  input("login with your new password Here: ")
                    print("\n")
                    if user_password == cloud_pass:
                        return cloud_dict
            
            if response == "n":
                return "n"       
                
# Creates or updates calendar under specific user.                 
def create_cal(db,cloud_cred, user):
    calendar_name = input("What do you want to call this Calendar: ")
    calendar_name = calendar_name.upper()
    new_cal_name = user + "_" + calendar_name
    result = db.collection("Calendars").document(new_cal_name).get()
    if result.exists:
        # Keeps user info up to date.
        db.collection("Calendars").document(new_cal_name).set(cloud_cred)
        username = {"username": user}
        db.collection("Calendars").document(new_cal_name).update(username)
    else:
        # Adds user keys to keep track of calendars     
        db.collection("Calendars").document(new_cal_name).set(cloud_cred)
        username = {"username": user}
        db.collection("Calendars").document(new_cal_name).update(username)
    
    choice = input("Would You like to add an event to your Calendar (y/n)? ")
    choice == choice.lower()
    if choice == "y":
        # Calls create events function so user can add events to new calendar right away.
        create_events(db,cloud_cred, user)
        return new_cal_name
    if choice == "n":   
        return new_cal_name

# Allows user to add an event to a specific day on a specific calendar.     
def create_events(db,cloud_cred, user):
    # Get data to create
    cal = input("What Calendar are you adding to: ")
    cal = cal.upper()
    new_cal = user + "_" + cal
    cal_test = db.collection("Calendars").document(new_cal).get()
    if cal_test.exists: 
        print("What date is the Event on?")
        date = input("(Format Ex: (Monday, May 4th 2021): ")
        user_date = user + "_" + date
        time = input("What Time is the Event at? : ")
        item = input("What is the event? : ")
        result = db.collection("Events").document(user_date).get()
        if result.exists:
            # Updates info if date exsists and adds user ID's for refrencing.
            db.collection("Events").document(user_date).update(cloud_cred)
            username = {"username" : user}
            db.collection("Events").document(user_date).update(username)
            cal_id = {"Cal_ID" : new_cal}
            db.collection("Events").document(user_date).update(cal_id)
            event = {time: item}
            db.collection("Events").document(user_date).update(event)
        else:
            # Creates new and adds user ID's for refrencing.
            event = {time: item}
            db.collection("Events").document(user_date).set(event)
            db.collection("Events").document(user_date).update(cloud_cred)
            username = {"username" : user}
            db.collection("Events").document(user_date).update(username)
            cal_id = {"Cal_ID" : new_cal}
            db.collection("Events").document(user_date).update(cal_id)
    else:
        # Makes sure user does not put even on non exisistant calendar.
        choice = input("This calendar does not exisit yet, would you like to create it (y/n)? ")
        if choice == "y":
            create_cal(db,cloud_cred, user)
        if choice == "n":   
            return   

# View options for user access to stored data.
def view(db,cloud_cred, user):
    print("What would you like to view?")
    print("1) All your events 2) A calendar 3) Events on a Specific date")
    response = input("> ")
    
    # Gets all events with the user ID and password. 
    if response == "1":
        cloud_pass = cloud_cred.get("password")
        # Searches only events with the user ID and Pass.
        query = db.collection("Events").where("password", "==", cloud_pass).where("username", "==", user)
        docs = query.stream()
        for doc in docs:
            # Run through events and pull out all keys. 
            events = doc.to_dict()
            cal = events["Cal_ID"]
            cals = cal.split("_")
            print(cals[1])
            date = str(doc.id)
            dates = date.split("_")
            print(dates[1])
            # Remove what we don't want to display. 
            del events["Cal_ID"]
            del events["password"]
            del events["username"]
            print ("\t{:<10}{:<10}".format("Time:","Event:"))
            print("\n".join("\t{:<10}{:<10}".format(k, v) for k, v in events.items()))
            print("\n")
    
    # Pulls events only by calendar ID.    
    if response == "2":
        cal = input("Which calendar would you like to view: ")
        cal = cal.upper()
        cal_id = user + "_" + cal
        # Searches only events with this Calendar ID.  
        query = db.collection("Events").where("Cal_ID", "==", cal_id)
        docs = query.stream()
        print('\n\033[1m' + cal)
        for doc in docs:
            # Run through events and pull out all keys.
            date = str(doc.id)
            dates = date.split("_")
            print ('\033[0m'+dates[1])
            events = doc.to_dict()
            # Remove what we don't want to display.
            del events["Cal_ID"]
            del events["password"]
            del events["username"]
            print ("\t{:<10}{:<10}".format("Time:","Event:"))
            print("\n".join("\t{:<10}{:<10}".format(k, v) for k, v in events.items()))
            print("\n")
    
    # Gets only events from a specific date.         
    if response == "3":
        print ("Which date would you like to view?")
        date = input("(Format Ex: (Monday, May 4th 2021): ")
        cloud_pass = cloud_cred.get("password")
         # Searches only events with The user and pass, AND only this date. 
        query = db.collection("Events").where("password", "==", cloud_pass).where("username", "==", user)
        docs = query.stream()
        for doc in docs:
            # Run through events and pull out all keys.
            date_id = str(doc.id)
            date_ids = date_id.split("_")
            if date_ids[1] == date:
                print(date_ids[1])
                events = doc.to_dict()
                # Remove what we don't want to display.
                del events["Cal_ID"]
                del events["password"]
                del events["username"]
                print ("\t{:<10}{:<10}".format("Time:","Event:"))
                print("\n".join("\t{:<10}{:<10}".format(k, v) for k, v in events.items()))
                print("\n")

# Allows user to remove database info only related to them. 
def delete(db,cloud_cred, user):
    print("What would you like to delete?")
    print("1) User 2) Calendar 3) All Events 4) A Date 5) An Event")
    response = input("> ") 
    
    # Detletes everything related to this user. 
    if response == "1":
        choice = input("Would you really like to delete your access (y/n)? ")
        choice == choice.lower()
        
        if choice == "y":
            db.collection("Users").document(user).delete()
            cloud_pass = cloud_cred.get("password")
            # Find everything with user tag. 
            query = db.collection("Events").where("password", "==", cloud_pass).where("username", "==", user)
            docs = query.stream()
            for doc in docs:
                db.collection("Events").document(doc.id).delete()
            query = db.collection("Calendars").where("password", "==", cloud_pass).where("username", "==", user)
            docs = query.stream()
            for doc in docs:
                db.collection("Calendars").document(doc.id).delete()
            print ("Delted all user data\n")
                
        if choice == "n":   
            return
    
    # Deletes all realted to this Calendar ID.     
    if response == "2":
        cal = input("What Calendar whould you like to delete: ")
        cal = cal.upper()
        new_cal = user + "_" + cal
        db.collection("Calendars").document(new_cal).delete()
         # Find everything with Calendar tag. 
        query = db.collection("Events").where("Cal_ID", "==", new_cal)
        docs = query.stream()
        for doc in docs:
            db.collection("Events").document(doc.id).delete()
        print("Deleted your Calendar and its Events\n")
    
    # All events related to this user.               
    if response == "3":
        print ("This will delete all events under yor username")
        cloud_pass = cloud_cred.get("password")
         # Find everything with The user ID and Pass. 
        query = db.collection("Events").where("password", "==", cloud_pass).where("username", "==", user)
        docs = query.stream()
        for doc in docs:
            # Only deletes events but not user info. 
            db.collection("Events").document(doc.id).delete()
        print("Deleted all Events\n")
    
    # Delets all realted to this Date.     
    if response == "4":
        print ("Which date would you like to delete?")
        date = input("(Format Ex: (Monday, May 4th 2021): ")
        user_date = user + "_" + date
        # Find everything with the date. 
        db.collection("Events").document(user_date).delete()
        print("Deleted Date and its Events\n")
    
    # Deletes just one Event.     
    if response == "5":
        print("This will delete one Event of your choice.\n")
        print("What date is the Event on?")
        date = input("(Format Ex: (Monday, May 4th 2021): ")
        user_date = user + "_" + date
        time = input("What Time is the Event at? : ")
        # Find the event and remove it. 
        deletion = db.collection("Events").document(user_date)
        deletion.update({time: firestore.DELETE_FIELD})
        print("Deleted event\n")    

# Calles all functions based on user descision.                    
def main(): 
    user = input("Enter your useranme Here: ")
    cloud_cred = validate(user)
    if cloud_cred == "n":
        print ('Thank you, Goodbye!')
        return
    exit = False
    while not exit:
        # Runs until user is done. 
        print ("Hello! " "What would you like to do with your calendar?")
        print ("Menu: A) Create Calendar B) Add Event C) Viewing Options D) Delete Q) Quit")
        response = input("> ")
        response = response.upper() 
        if response == "A":
           print("\n")
           create_cal(db,cloud_cred, user)
           print("\n")

        if response == "B":
            print("\n")
            create_events(db,cloud_cred, user)
            print("\n")    
           
        if response == "C":
            print("\n")
            view(db,cloud_cred, user)
        
        if response == "D":
            print("\n")
            delete(db,cloud_cred, user)
        
        if response == "Q":  
            exit = True
# Run Main.            
main()