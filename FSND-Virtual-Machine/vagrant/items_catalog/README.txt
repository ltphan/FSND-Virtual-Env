Clone this project by typing this command:
git clone https://github.com/ltphan/FSND-Virtual-Env.git

Steps to run this project:
1. Go to vacant environment and ssh into virtual machine using the following commands:
vagrant up
vagrant ssh

2. Once logged into VM, use the following command to enter the directory of the project:
cd /vagrant/items_catalog

3. Once in directory, run following commands to initialize and populate the Database:
python database_setup.py
python lotsofitems.py

4. Once you have run the above commands successfully, you should see an itemscatalog.db named file in your local directory /items_catalog

5. Run the following command to run the app:
python finalProject.py