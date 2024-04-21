from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .models import Profile, Expense
from django.contrib.auth import logout
from datetime import date

from django.contrib.auth.decorators import login_required

# Create your views here.
def index(request):
    if request.method == 'POST':
        # authenticate the user
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  
            #return HttpResponse("Login successful!")
        else:
            return HttpResponse("Login failed. Invalid credentials.")
    return render(request, 'index.html')


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        name = request.POST.get('name')
        monthly_budget = request.POST.get('monthly_budget')
        # Check if username is already taken
        if User.objects.filter(username=username).exists():
            return HttpResponse("Username already exists. Please choose a different one.")
        # Create the user
        user = User.objects.create_user(username=username, email=email, password=password)
        # Create the profile
        profile = Profile.objects.create(user=user, name=name, monthly_budget=monthly_budget)
        # Log the user in
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")  # Or redirect to another page
        else:
            return HttpResponse("Error occurred during registration.")
    else:
        # Render the registration form template
        return render(request, 'register.html')

#VIEW FUNCTIONS FOR READING DATA FROM CSV FILE--------------------------------------------------
import csv
from io import TextIOWrapper
def import_data_from_csv(csv_file, user):
    try:
        # Open the CSV file in text mode
        csv_reader = csv.DictReader(TextIOWrapper(csv_file, encoding='utf-8'))
        for row in csv_reader:
            date_str = row['Date']
            date_obj = datetime.strptime(date_str, '%d-%m-%Y').strftime('%Y-%m-%d')
            Expense.objects.create(
                user=user,
                date=date_obj,
                category=row['Category'],
                amount=row['Amount']
            )
        return True
    except Exception as e:
        print(f"Error importing data from CSV: {e}")
        return False

def csvView(request):
    if request.method == 'POST':
        print(request.FILES)
        if 'csv_file' in request.FILES:
            user = request.user  # Retrieve the authenticated user
            csv_file = request.FILES['csv_file']
            try:
                success = import_data_from_csv(csv_file, user)
                if success:
                    return HttpResponse("Data imported successfully.")
                else:
                    return HttpResponse("Error importing data from CSV.")
            except Exception as e:
                return HttpResponse(f"An error occurred: {e}")
        else:
            return HttpResponse("No file uploaded.")
    else:
        return render(request, 'csvupload.html')

#VIEW FUNCTION FOR AIML------------------------------------------------------
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta
import statistics

def utility(user):
    current_month = date.today().month
    current_year = date.today().year
    num_days = calendar.monthrange(current_year, current_month)[1]
    x = list(range(1, num_days + 1))
    # user = request.user
    expenses = Expense.objects.filter(user=user, date__month=current_month, date__year=current_year)
    amount_spent_per_day = {day: 0 for day in x}
    #bar plot
    for expense in expenses:
        amount_spent_per_day[expense.date.day] += expense.amount
    y = [amount_spent_per_day[day] for day in x]
    plt.figure(figsize=(8, 6))
    bar_width = 0.4
    bars = plt.bar(x, y, width=bar_width)
    plt.xlabel('Days')
    plt.ylabel('Amount Spent')
    plt.title(f'Amount spent each day in {calendar.month_name[current_month]},{current_year}')
    plt.xticks(x, rotation=90)
    for bar, amount in zip(bars, y):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5, str(int(amount)), ha='center')
    buffer1 = BytesIO()
    plt.savefig(buffer1, format='png')
    buffer1.seek(0)
    bar_plot_image = base64.b64encode(buffer1.getvalue()).decode('utf-8')
    buffer1.close()
    #pie chart
    categories = expenses.values_list('category', flat=True).distinct()
    total_spent_per_category = {category: 0 for category in categories}
    for expense in expenses:
        total_spent_per_category[expense.category] += expense.amount
    plt.figure(figsize=(8, 6))
    plt.pie(total_spent_per_category.values(), labels=total_spent_per_category.keys(), autopct='%1.1f%%')
    plt.title(f'Percentage of Expenses by Category in {calendar.month_name[current_month]},{current_year}')
    buffer2 = BytesIO()
    plt.savefig(buffer2, format='png')
    buffer2.seek(0)
    pie_chart_image = base64.b64encode(buffer2.getvalue()).decode('utf-8')
    buffer2.close()
    return {'bar_plot_image': bar_plot_image,'pie_chart_image': pie_chart_image}
    

@login_required
def ai_view(request): 
    if request.method=='POST':
        startdate = request.POST.get('startdate')
        enddate = request.POST.get('enddate')
        #FORM SUBMITTED WITHOUT INPUT VALUES
        if not startdate or not enddate:
            user=request.user 
            dict=utility(user) 
            return render(request, 'aiml.html', dict)
    
    #DEFAULT PAGE VIEW COMPONENTS SHOWING CURRENT MONTH'S EXPENSES
    else:
        user=request.user 
        dict=utility(user) 
        return render(request, 'aiml.html', dict)      
    
    startdate=parse_date(startdate)
    enddate=parse_date(enddate)
    x = []
    current_date = startdate
    while current_date <= enddate:
        x.append(current_date)
        current_date += timedelta(days=1)
    user = request.user
    expenses = Expense.objects.filter(user=user, date__range=[startdate, enddate])
    amount_spent_per_day = {day: 0 for day in x}
    for expense in expenses:
        amount_spent_per_day[expense.date] += expense.amount
    y = [amount_spent_per_day[day] for day in x]
    #BAR PLOT
    plt.figure(figsize=(20, 10))
    bar_width = 0.4
    bars = plt.bar(x, y, width=bar_width)
    plt.ylabel('Amount Spent',fontsize=20)
    plt.xticks(x, rotation=90)
    for bar, amount in zip(bars, y):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5, str(int(amount)), ha='center',fontsize=15)
    buffer1 = BytesIO()
    plt.savefig(buffer1, format='png')
    buffer1.seek(0)
    bar_plot_image = base64.b64encode(buffer1.getvalue()).decode('utf-8')
    buffer1.close()
    # PIE CHART
    categories = expenses.values_list('category', flat=True).distinct()
    total_spent_per_category = {category: 0 for category in categories}
    for expense in expenses:
        total_spent_per_category[expense.category] += expense.amount
    plt.figure(figsize=(20, 10))
    plt.pie(total_spent_per_category.values(), labels=total_spent_per_category.keys(), autopct='%1.1f%%',radius=1.3,textprops={'fontsize':20})
    buffer2 = BytesIO()
    plt.savefig(buffer2, format='png')
    buffer2.seek(0)
    pie_chart_image = base64.b64encode(buffer2.getvalue()).decode('utf-8')
    buffer2.close()
    #quantitative analysis
    largest_value = max(amount_spent_per_day.values())
    largest_key = max(amount_spent_per_day, key=amount_spent_per_day.get)
    # largest_key=(key for key, val in amount_spent_per_day.items() if val == largest_value)
    smallest_value = min(value for value in amount_spent_per_day.values() if value != 0)
    smallest_key = min(amount_spent_per_day, key=amount_spent_per_day.get)
    # Calculate the average
    average_value = round(sum(amount_spent_per_day.values()) / len(amount_spent_per_day),2)
    # Calculate the median
    median_value = round(statistics.median(value for value in amount_spent_per_day.values() if value != 0), 2)
    stats={
        'max':[largest_key,largest_value],
        'min':[smallest_key,smallest_value],
        'avg':[None,average_value],
        'median':[None,median_value]
    }
    return render(request, 'aiml.html', {'bar_plot_image': bar_plot_image,'pie_chart_image': pie_chart_image,'startdate':startdate,'enddate':enddate,'stats':stats})

#FUNCTION FOR HISTORY-----------------------------------------------------
from collections import defaultdict
@login_required
def history_view(request):
    # Retrieve all expenses for the current user
    if request.method=='POST':
        startdate = parse_date(request.POST.get('startdate'))
        enddate = parse_date(request.POST.get('enddate'))
        if not startdate or not enddate:
            user_expenses = Expense.objects.filter(user=request.user)
        else:
            user_expenses = Expense.objects.filter(user=request.user, date__range=[startdate, enddate])
    else:
        user_expenses = Expense.objects.filter(user=request.user)
        startdate,enddate=None,None
    expenses_by_month = defaultdict(list)
    for expense in user_expenses:
        month_year = expense.date.strftime('%B %Y')
        expenses_by_month[month_year].append(expense)
    sorted_expenses_by_month = dict(sorted(expenses_by_month.items(), key=lambda x: datetime.strptime(x[0], '%B %Y'), reverse=True))
    if not startdate and not enddate:
        return render(request, 'history.html', {'expenses_by_month': sorted_expenses_by_month})
    return render(request, 'history.html', {'expenses_by_month': sorted_expenses_by_month,'startdate':startdate,'enddate':enddate})
    

#FUNCTION FOR ADD EXPENSE-----------------------------------------------------
@login_required
def add_expense(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        category = request.POST.get('category')
        date_str = request.POST.get('date')
        
        # If date is provided, use it; otherwise, use today's date
        if date_str:
            date_obj = date.fromisoformat(date_str)
        else:
            date_obj = date.today()
        
        user = request.user

        # Create expense object
        Expense.objects.create(user=user, amount=amount, category=category, date=date_obj)

        # Redirect to home page or any other page after adding the expense
        return redirect('home')  # Change 'home' to the name of your home page URL pattern
    else:
        return render(request, 'home.html')
    

#FUNCTION FOR LOGOUT-----------------------------------------------------  
def logout_view(request):
    logout(request)
    return redirect('index')  


#FUNCTION FOR PROFILE-----------------------------------------------------
@login_required
def profile_view(request):
    user = request.user
    profile = Profile.objects.get(user=user)

    if request.method == 'POST':
        monthly_budget = request.POST.get('monthly_budget')
        profile.monthly_budget = monthly_budget
        profile.save()
        return redirect('home')  # Redirect to the profile page after successfully updating the budget

    return render(request, 'profile.html', {'user': user, 'profile': profile})



from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime, date
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from .models import Expense

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime, date
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from .models import Expense

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime, date
import pandas as pd
from io import BytesIO
import base64
from .models import Expense

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import calendar

#FUNCTION FOR HOME-----------------------------------------------------
@login_required
def home_view(request):
    # Get the current month and year
    current_month = date.today().month
    current_year = date.today().year

    # Calculate the number of days in the current month
    num_days = calendar.monthrange(current_year, current_month)[1]

    # Create x-axis values (days of the month)
    x = list(range(1, num_days + 1))

    # Get the user's expenses for the current month
    user = request.user
    expenses = Expense.objects.filter(user=user, date__month=current_month, date__year=current_year)

    # Create a dictionary to store the amount spent each day
    amount_spent_per_day = {day: 0 for day in x}

    # Calculate the amount spent for each day
    for expense in expenses:
        amount_spent_per_day[expense.date.day] += expense.amount

    # Convert the dictionary values to a list of amounts for plotting
    y = [amount_spent_per_day[day] for day in x]

    # Plot the amount spent each day as a bar graph
    plt.figure(figsize=(8, 6))
    bar_width = 0.4
    bars = plt.bar(x, y, width=bar_width)
    plt.xlabel('Days')
    plt.ylabel('Amount Spent')
    plt.title('Amount Spent Each Day')

    # Set x-axis tick locations to display all values
    plt.xticks(x, rotation=90)
    for bar, amount in zip(bars, y):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5, str(int(amount)), ha='center')

    # Convert the bar plot to a PNG image
    buffer1 = BytesIO()
    plt.savefig(buffer1, format='png')
    buffer1.seek(0)
    bar_plot_image = base64.b64encode(buffer1.getvalue()).decode('utf-8')
    buffer1.close()

    # Create a pie chart for expense categories
    categories = expenses.values_list('category', flat=True).distinct()
    total_spent_per_category = {category: 0 for category in categories}
    for expense in expenses:
        total_spent_per_category[expense.category] += expense.amount

    # Plot the pie chart
    plt.figure(figsize=(8, 6))
    plt.pie(total_spent_per_category.values(), labels=total_spent_per_category.keys(), autopct='%1.1f%%')
    plt.title('Percentage of Expenses by Category')

    # Convert the pie chart to a PNG image
    buffer2 = BytesIO()
    plt.savefig(buffer2, format='png')
    buffer2.seek(0)
    pie_chart_image = base64.b64encode(buffer2.getvalue()).decode('utf-8')
    buffer2.close()
    
    # sum the total amount spent and subtract from monthly budget
    total_spent = sum(y)
    monthly_budget = Profile.objects.get(user=user).monthly_budget
    remaining_budget = monthly_budget - total_spent
    

    # Render the template with the plot images
    return render(request, 'home.html', {'bar_plot_image': bar_plot_image, 
                                         'pie_chart_image': pie_chart_image, 
                                         'remaining_budget': remaining_budget,
                                         'total_spent': total_spent,
                                          'monthly_budget': monthly_budget,
                                          'username': user.username})
