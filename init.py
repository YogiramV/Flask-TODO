from flask import Flask

from flask import render_template,request,redirect,session
from flask_session import Session
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
import datetime


app = Flask(__name__)
socketio = SocketIO(app, ping_interval=10, ping_timeout=30)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://yogi:0N4KhCjULTvHxFap9bi0e20Sls5wxpuy@dpg-cj9j9im3ttrc73d470r0-a/todo_a43z"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Session(app)


####DB#####

class USER(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String)
    age = db.Column(db.Integer)
    username = db.Column(db.String,unique=True,nullable=False)
    password = db.Column(db.Integer)
    role = db.Column(db.String)
    manager = db.Column(db.String)

    tasks = db.relationship('TASKS', backref='USER')

class TASKS(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    task_id = db.Column(db.Integer,primary_key=True)
    task_name = db.Column(db.String)
    duedate = db.Column(db.DateTime)
    status = db.Column(db.String)
    remarks = db.Column(db.String)

    room = db.relationship('CHATROOM', backref='TASKS')

class CHATROOM(db.Model):
    room_id = db.Column(db.Integer,primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.task_id'))
    manager_id = db.Column(db.Integer)
    employee_id = db.Column(db.Integer)

    messages= db.relationship('MESSAGES', backref='CHATROOM')

class MESSAGES(db.Model):
    message_id = db.Column(db.Integer,primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('chatroom.room_id'))
    sender = db.Column(db.String)
    message = db.Column(db.String)

with app.app_context():
    db.create_all()
###########


@app.route('/')
def actions():
    if session.get("username"):
        return render_template("home.html")
    return render_template("actions.html")

@app.route('/home')
def home():
    if session.get("username"):
        role = session.get("role")
        return render_template("home.html",role=role)
    return """<script>
                    if (window.confirm('Login required. Please login to your account.')) 
                    {
                        window.location.href='/sign-in';
                    };
              </script>"""


@app.route('/resetdb')
def resetdb():
    db.session.query(USER).delete()
    db.session.query(TASKS).delete()
    db.session.commit()

    return """<script>
                    if (window.confirm('User database is reset')) 
                    {
                        window.location.href='/';
                    };
              </script>"""

@app.route('/logout')
def logout():
    print("Username stored in session :", session["username"])
    session["username"]=None #Setting username as none because user is logged off currently
    session["userid"]=None
    session["role"]=None
    return """<script>
                    if (window.confirm('Successsfully logged out')) 
                    {
                        window.location.href='/';
                    };
              </script>"""

@app.route('/sign-up',methods=["GET","POST"])
def sign_up():
    if request.method == "POST":
        req = request.form
        name = req["name"]
        age = req["age"]
        username = req["username"]
        password = req["password"]
        role = req["role"]
        manager = req["manager"]
        if userExists(username):
            return """<script>
                        if (window.confirm('User already exists, please sign-in with your account')) 
                        {
                            window.location.href='/sign-in';
                        };
                    </script>"""

        else:
            storeDetails(name,age,username,password,role,manager)
        return redirect("/sign-in")
    managers=getManagers()
    print("MANAGERS : ",managers)
    return render_template("sign_up.html",managers=managers)

def getManagers():
    managers = db.session.query(USER.name).filter_by(role="MANAGER").all()
    managers = [manager for manager, in managers]
    print(managers)

    return managers



@app.route('/sign-in',methods=["GET","POST"])
def sign_in():
    if session.get("username"):
        print("User in session: ", session["username"])
        print("User ID: ", session["userid"])
        return """<script>
                    if (window.confirm('Signed in successfully.')) 
                    {
                        window.location.href='/home';
                    };
                    </script>"""
    
    if request.method == "POST":
        if isAdminUser(request.form["username"],request.form["password"]):
                return """<script>
                    if (window.confirm('Signed in as ADMIN successfully.')) 
                    {
                        window.location.href='/home';
                    };
                    </script>"""

        if userExists(request.form["username"]) :
            if correctPassword(request.form["username"],request.form["password"]):
                session["username"] = request.form["username"]
                session["userid"] = getIDFromName(request.form["username"])
                session["role"] = getRoleFromName(request.form["username"])
                return """<script>
                    if (window.confirm('Signed in successfully.')) 
                    {
                        window.location.href='/home';
                    };
                    </script>"""
            else:
                return """<script>
                    if (window.confirm('Incorrect Password')) 
                    {
                        window.location.href='/sign-in';
                    };
                    </script>"""
        else:
            return """<script>
                    if (window.confirm('User does not exist. Please register your account.')) 
                    {
                        window.location.href='/sign-up';
                    };
                    </script>"""
        
    return render_template("sign_in.html")

def isAdminUser(username,password):
    if username == "admin" and password == "admin":
        session["username"] = "admin"
        session["userid"] = getIDFromName(request.form["username"])
        session["role"] = "ADMIN"
        return True
    else:
        return False

def getIDFromName(username):
    ID=db.session.query(USER.id).filter_by(username=username).scalar()
    print("ID :", ID)
    return ID

def getRoleFromName(username):
    role=db.session.query(USER.role).filter_by(username=username).scalar()
    print("ROLE :", role)
    return role

def storeDetails(name,age,username,password,role,manager):
    db.session.add(USER(name = name,age = age,username = username,password = password,role = role,manager =manager))
    db.session.commit()

def userExists(username):
    Users=db.session.query(USER.username).all()
    Users = [user for user, in Users]
    print("Users :", Users)
    if username in Users:
        return True
    else:
        return False
    
def correctPassword(username,password):
    print("Checking for :", password)
    fetchedPassword=db.session.query(USER.password).filter_by(username=username).scalar()


    print("Password :", fetchedPassword)
    if password == str(fetchedPassword):
        return True
    else:
        return False
    
@app.route('/create')
def create():
    role = session["role"]
    if role == "ADMIN":
        employees = fetchAllEmployees()
    else:
        employees= fetchEmployees(session["userid"])
    print(role)
    print(employees)
    return render_template("create.html",role=role,employees=employees)
    
@app.route('/task/create',methods=["GET","POST"])
def createTask():
    if request.method == "POST":
        req = request.form
        taskname = req["taskname"]
        duedate = req["duedate"]
        status = req["status"]
        remarks = req["remarks"]
        print(req["employee"])
        empid = getIDFromName(req["employee"])
        print(status)
        storeTaskDetails(empid,taskname,duedate,status,remarks)
        return """<script>
                    if (window.confirm('Task created successfully.')) 
                    {
                        window.location.href='/home';
                    };
                    </script>"""
    role = session["role"]
    employees= fetchEmployees(session["userid"])
    print(employees)
    return render_template("create.html",role=role,employees=employees)

def storeTaskDetails(empid,taskname,duedate,status,remarks):

    date = datetime.date.fromisoformat(duedate)

    db.session.add(TASKS(user_id = empid,task_name = taskname,duedate = date,status = status,remarks = remarks))
    db.session.commit()

@app.route('/view/<userid>')
def viewTaskForID(userid):
    tasks= fetchTasks(userid)

    return render_template("viewtasks.html",tasks=tasks,role=session["role"],action="no")

@app.route('/view')
def viewTask():
    userid = session["userid"]

    if session["role"] == "EMPLOYEE":
        tasks= fetchTasks(userid)
    elif session["role"] == "MANAGER":
        tasks= fetchTasksForManager(userid)
    else:
        tasks= fetchAllTasks()
    return render_template("viewtasks.html",tasks=tasks,role=session["role"])

def fetchTasks(userid):

    contents = db.session.query(TASKS).join(USER).filter(USER.id==userid).all()
    list=[]
    for con in contents:
        list.append([con.user_id,con.task_id,con.task_name,con.duedate,con.status,con.remarks])

    return list

def fetchTasksForManager(userid):

    name = db.session.query(USER.name).filter_by(id=userid).scalar() 
    print(name)
    contents = db.session.query(TASKS).join(USER).filter_by(manager=name).all()
    list=[]
    for con in contents:
        list.append([con.user_id,con.task_id,con.task_name,con.duedate,con.status,con.remarks])
    print(list)
    contents = db.session.query()

    return list

def fetchAllTasks():

    contents = db.session.query(TASKS).all()
    list=[]
    for con in contents:
        list.append([con.user_id,con.task_id,con.task_name,con.duedate,con.status,con.remarks])

    return list

@app.route('/update/<taskid>')
def updatePage(taskid):
    role=session["role"]
    taskname=getTaskFromID(taskid)
    duedate=getDueFromID(taskid)
    return render_template("update.html",taskid=taskid,role=role,taskname=taskname,duedate=duedate)

def getTaskFromID(taskid):
    taskname = db.session.query(TASKS.task_name).filter_by(task_id=taskid).scalar()
    return taskname

def getDueFromID(taskid):
    due = db.session.query(TASKS.duedate).filter_by(task_id=taskid).scalar()
    return due

@app.route('/task/update/<taskid>',methods=["GET","POST"])
def updateTask(taskid):
    req = request.form
    if session["role"] == "EMPLOYEE":
        status = req["status"]
        updateTaskStatus(taskid,status)
        return """<script>
                if (window.confirm('Task updated successfully.')) 
                {
                    window.location.href='/view';
                };
                </script>"""
    else:
        taskname = req["taskname"]
        duedate = req["duedate"]
        status = req["status"]
        remarks = req["remarks"]
        updateTaskDetails(taskid,taskname,duedate,status,remarks)
        return """<script>
                    if (window.confirm('Task updated successfully.')) 
                    {
                        window.location.href='/view';
                    };
                    </script>"""
    

def updateTaskDetails(taskid,taskname,duedate,status,remarks):

    task = db.session.query(TASKS).filter_by(task_id=taskid).first()
    task.task_name = taskname
    task.duedate = datetime.date.fromisoformat(duedate)
    task.status = status
    task.remarks = remarks
    db.session.commit()

def updateTaskStatus(taskid,status):
    task = db.session.query(TASKS).filter_by(task_id=taskid).first()
    task.status = status
    db.session.commit()

@app.route('/task/delete/<taskid>')
def deleteTask(taskid):
    db.session.query(TASKS).filter_by(task_id=taskid).delete()
    db.session.commit()
    return """<script>
                    if (window.confirm('Task is deleted')) 
                    {
                        window.location.href='/view';
                    };
              </script>"""

@app.route('/employees')
def employees():
    if session["role"] == "ADMIN":
        employees=fetchAllEmployees()
    else :
        employees= fetchEmployees(session["userid"])
    print(employees)
    return render_template("employees.html",role=session["role"],employees=employees)

@app.route('/employees/<userid>')
def employeesForManager(userid):
    employees= fetchEmployees(userid)
    print(employees)
    return render_template("employees.html",role=session["role"],employees=employees)

def fetchEmployees(id):
    name = db.session.query(USER.name).filter_by(id=id).scalar()
    employees= db.session.query(USER).filter_by(manager=name).all()
    list=[]
    for emp in employees:
        list+=[[emp.id,emp.name,emp.age,emp.username,emp.password,emp.role,emp.manager]]

    return list
    
def fetchAllEmployees():
    employees= db.session.query(USER).filter_by(role="EMPLOYEE").all()
    list=[]
    for emp in employees:
        list.append([emp.id,emp.name,emp.age,emp.username,emp.password,emp.role,emp.manager])

    return list

def fetchAllManagers():
    employees= db.session.query(USER).filter_by(role="MANAGER").all()
    list=[]
    for emp in employees:
        list.append([emp.id,emp.name,emp.age,emp.username,emp.password,emp.role,emp.manager])
    print(list,"asdsdasd")

    return list

@app.route('/managers')
def managers():
    managers= fetchAllManagers()
    print(managers)
    return render_template("managers.html",role=session["role"],managers=managers)

@app.route('/chat/<taskid>')
def openchat(taskid):
    role = session["role"]
    if role == "MANAGER":
        managerid = session["userid"]
        empid = getTaskOwner(taskid)
        
    else :
        empid = session["userid"]
        managerid = getManager(empid)
    
    if getRoomID(taskid) == None:
        createChatRoom(taskid,managerid,empid)
    
    roomid = getRoomID(taskid)
    session["roomid"]=roomid

    messages = getMessages(roomid)

    return render_template('chatroom.html', messages=messages)

def getRoomID(taskid):
    roomid= db.session.query(CHATROOM.room_id).join(TASKS).filter_by(task_id=taskid).scalar()
    return roomid

def createChatRoom(taskid,managerid,empid):
    db.session.add(CHATROOM(task_id = taskid,manager_id = managerid,employee_id = empid))
    db.session.commit()

def getTaskOwner(taskid):
    empid = db.session.query(TASKS.user_id).filter_by(task_id=taskid).scalar()
    return empid

def getManager(empid):
    name = db.session.query(USER.manager).filter_by(id=empid).scalar()
    managerid = db.session.query(USER.id).filter_by(name=name).scalar()
    return managerid




def getMessages(roomid):
    messages= db.session.query(MESSAGES).filter_by(room_id=roomid).all()
    print(messages)
    list=[]
    for mes in messages:
        list.append([mes.message_id,mes.room_id,mes.sender,mes.message])

    return list


@socketio.on('message')
def handleMessage(data):
    message = data['message']
    saveMessage(message)
    emit('message', {'message': message}, broadcast=True)


def saveMessage(message):
    sender=getUserFromID(session["userid"])
    db.session.add(MESSAGES(room_id = session["roomid"],sender = sender,message = message))
    db.session.commit()

def getUserFromID(empid):
    user = db.session.query(USER.name).filter_by(id=empid).scalar()
    return user

@app.route('/chat/clear')
def clearChat():
    db.session.query(MESSAGES).delete()
    db.session.commit()
    return """<script>
                if (window.confirm('Messages are deleted')) 
                {
                    window.location.href='/view';
                };
            </script>"""
