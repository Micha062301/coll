//A simple C++ budget tracker to manage expenses, track income, and stay financially organized.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
 
#define MAX_TRANSACTIONS 1000
#define MAX_CATEGORIES 50
#define MAX_NAME_LENGTH 50
#define MAX_DESC_LENGTH 100
#define MAX_NOTIFICATIONS 50
 
typedef struct {
   char message[100];
   time_t timestamp;
   int is_read;
} Notification;
 
typedef struct {
   char name[MAX_NAME_LENGTH];
   float budget_limit;
   float current_spent;
} Category;
 
typedef struct {
   float amount;
   char description[MAX_DESC_LENGTH];
   char category[MAX_NAME_LENGTH];
   time_t timestamp;
   int is_income;
} Transaction;
 
typedef struct {
   Transaction transactions[MAX_TRANSACTIONS];
   Category categories[MAX_CATEGORIES];
   Notification notifications[MAX_NOTIFICATIONS];
   int transaction_count;
   int category_count;
   int notification_count;
   float total_income;
   float total_expenses;
} BudgetTracker;
 
void clear_input_buffer() {
   int c;
   while ((c = getchar()) != '\n' && c != EOF);
}
 
float get_float_input(const char *prompt) {
   float value;
   printf("%s", prompt);
   while (scanf("%f", &value) != 1) {
       printf("Invalid input. Please enter a number: ");
       clear_input_buffer();
   }
   clear_input_buffer();
   return value;
}
 
void get_string_input(char *buffer, int max_length, const char *prompt) {
   printf("%s", prompt);
   fgets(buffer, max_length, stdin);
   buffer[strcspn(buffer, "\n")] = 0;
}
 
void init_tracker(BudgetTracker *tracker) {
   tracker->transaction_count = 0;
   tracker->category_count = 0;
   tracker->notification_count = 0;
   tracker->total_income = 0;
   tracker->total_expenses = 0;
 
   const char *default_categories[] = {
       "Salary", "Freelance", "Investments",
       "Food", "Transport", "Utilities", "Rent", "Entertainment"
   };
 
   for (int i = 0; i < sizeof(default_categories) / sizeof(default_categories[0]); i++) {
       strcpy(tracker->categories[i].name, default_categories[i]);
       tracker->categories[i].budget_limit = 0;
       tracker->categories[i].current_spent = 0;
       tracker->category_count++;
   }
 
   strcpy(tracker->notifications[tracker->notification_count++].message,
          "Tracker initialized with default categories.");
}
 
void add_income(BudgetTracker *tracker) {
   if (tracker->transaction_count >= MAX_TRANSACTIONS) {
       printf("Transaction limit reached!\n");
       return;
   }
   Transaction *t = &tracker->transactions[tracker->transaction_count];
   t->amount = get_float_input("Enter income amount: ");
   get_string_input(t->description, MAX_DESC_LENGTH, "Enter income description: ");
   strcpy(t->category, "Income");
   t->timestamp = time(NULL);
   t->is_income = 1;
 
   tracker->total_income += t->amount;
   tracker->transaction_count++;
 
   printf("Income added successfully!\n");
}
 
void add_expense(BudgetTracker *tracker) {
   if (tracker->transaction_count >= MAX_TRANSACTIONS) {
       printf("Transaction limit reached!\n");
       return;
   }
   Transaction *t = &tracker->transactions[tracker->transaction_count];
   t->amount = get_float_input("Enter expense amount: ");
   printf("Select category:\n");
   for (int i = 0; i < tracker->category_count; i++) {
       printf("%d. %s\n", i + 1, tracker->categories[i].name);
   }
   int category_choice;
   scanf("%d", &category_choice);
   clear_input_buffer();
 
   if (category_choice < 1 || category_choice > tracker->category_count) {
       printf("Invalid category. Expense not recorded.\n");
       return;
   }
   strcpy(t->category, tracker->categories[category_choice - 1].name);
   tracker->categories[category_choice - 1].current_spent += t->amount;
 
   if (tracker->categories[category_choice - 1].budget_limit > 0 &&
       tracker->categories[category_choice - 1].current_spent >
           tracker->categories[category_choice - 1].budget_limit) {
       printf("Warning: You exceeded the budget for %s!\n",
              tracker->categories[category_choice - 1].name);
   }
 
   get_string_input(t->description, MAX_DESC_LENGTH, "Enter expense description: ");
   t->timestamp = time(NULL);
   t->is_income = 0;
 
   tracker->total_expenses += t->amount;
   tracker->transaction_count++;
 
   printf("Expense added successfully!\n");
}
 
void view_transactions(BudgetTracker *tracker) {
   if (tracker->transaction_count == 0) {
       printf("No transactions recorded.\n");
       return;
   }
 
   printf("Transactions:\n");
   printf("%-20s %-10s %-12s %-30s\n", "Category", "Amount", "Type", "Description");
   printf("-------------------------------------------------------------\n");
   for (int i = 0; i < tracker->transaction_count; i++) {
       Transaction *t = &tracker->transactions[i];
       printf("%-20s $%-9.2f %-12s %-30s\n", t->category, t->amount,
              t->is_income ? "Income" : "Expense", t->description);
   }
}
 
void set_budget(BudgetTracker *tracker) {
   printf("Set budget limits for categories:\n");
   for (int i = 0; i < tracker->category_count; i++) {
       printf("%s: Current limit $%.2f\n", tracker->categories[i].name,
              tracker->categories[i].budget_limit);
       tracker->categories[i].budget_limit =
           get_float_input("Enter new budget limit (0 for no limit): ");
   }
   printf("Budget limits updated.\n");
}
 
void add_notification(BudgetTracker *tracker, const char *message) {
   if (tracker->notification_count >= MAX_NOTIFICATIONS) {
       for (int i = 0; i < MAX_NOTIFICATIONS - 1; i++) {
           tracker->notifications[i] = tracker->notifications[i + 1];
       }
       tracker->notification_count--;
   }
   Notification *n = &tracker->notifications[tracker->notification_count++];
   strncpy(n->message, message, 99);
   n->timestamp = time(NULL);
   n->is_read = 0;
}
 
void view_notifications(BudgetTracker *tracker) {
   if (tracker->notification_count == 0) {
       printf("No notifications available.\n");
       return;
   }
 
   printf("Notifications:\n");
   for (int i = 0; i < tracker->notification_count; i++) {
       Notification *n = &tracker->notifications[i];
       printf("%s\n", n->message);
   }
}
 
void main_menu(BudgetTracker *tracker) {
   int choice;
   do {
       printf("1. Add Income\n");
       printf("2. Add Expense\n");
       printf("3. View Transactions\n");
       printf("4. Set Budget Limits\n");
       printf("5. View Notifications\n");
       printf("6. Exit\n");
       printf("Choose an option: ");
       scanf("%d", &choice);
       clear_input_buffer();
 
       switch (choice) {
           case 1:
               add_income(tracker);
               break;
           case 2:
               add_expense(tracker);
               break;
           case 3:
               view_transactions(tracker);
               break;
           case 4:
               set_budget(tracker);
               break;
           case 5:
               view_notifications(tracker);
               break;
           case 6:
               printf("Exiting. Goodbye!\n");
               break;
           default:
               printf("Invalid choice. Try again.\n");
       }
   } while (choice != 6);
}
 
int main() {
   BudgetTracker tracker;
   init_tracker(&tracker);
   main_menu(&tracker);
   return 0;
}
 