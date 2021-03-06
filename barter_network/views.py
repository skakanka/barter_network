"""Barter Network App"""
from barter_network import app
import random

from jinja2 import StrictUndefined

from flask import render_template, request, flash, redirect, session, jsonify

from sqlalchemy import func, desc
from model import connect_to_db, db, User, Skill, UserSkill
import bcrypt
import os
import geocoder
import helper_fun
import network
import ml
import numpy as np

import sys
sys.path.append('..')

from barter_network import app



app.jinja_env.undefined = StrictUndefined
app.jinja_env.auto_reload = True


app.secret_key = os.environ["APP_KEY"]
map_key = os.environ["GOOGLE_API_KEY"]



@app.route('/')
def index():
    """Homepage"""

    return render_template("homepage.html")


@app.route('/pagerank.json')
def pagerank():
    """Pagerank chart js"""
    data_dict = {
                "labels": network.node_names,
                "datasets": [
                    {
                        "data": network.page_rank,
                        "backgroundColor": network.random_col,
                      
                        "hoverBackgroundColor": network.random_col
                
                    }]
            }

    return jsonify(data_dict)

@app.route('/register', methods=['GET'])
def barter_up_form():
    """Sign Up form"""

    return render_template("barter_up_form.html",map_key_api=map_key)


@app.route('/register', methods=['POST'])
def barter_up_process():
    """Sign Up process"""

    email = request.form.get('email')
    password = request.form.get('password')
    fname = request.form.get('fname')
    lname = request.form.get('lname')
    dob = request.form.get('dob')
    occupation = request.form.get('occupation')
    zipcode = request.form.get('zipcode')
    street_address = request.form.get('street-address')
    city = request.form.get('city')
    state = request.form.get('state')

    g = geocoder.google(street_address+''+city+''+state)
    lat = g.latlng[0]
    lng = g.latlng[1]

    qry = db.session.query(func.max(User.user_occupation_id).label("max_score"))
    res = qry.one()
    oc_max = res.max_score


    if User.query.filter_by(user_email=email).first():
        flash('Please log in, you are alreday registered')

        return redirect('/login')
    else:
        oc_id = db.session.query(User.user_occupation_id).filter(User.user_occupation==occupation).first()
        
        if not oc_id:
            oc_id = oc_max+1
        
        new_user = User(user_fname=fname,user_lname=lname,
            user_zipcode=zipcode,user_street_address=street_address, user_city=city, user_state=state,user_dob=dob, user_occupation=occupation, 
            user_occupation_id= oc_id,user_email=email, user_password=bcrypt.hashpw(password.encode('UTF_8'), bcrypt.gensalt()), user_lat=lat, user_lng=lng)
        db.session.add(new_user)
        db.session.commit()

    session['user_id'] = new_user.user_id
    flash('You are now logged in!')
    helper_fun.add_node(network.Z, new_user.user_id,new_user.user_fname)

    # ml_skill_to,ml_skill_from = ml.predict(db.session.query(User.user_occupation_id).filter(User.user_id==session['user_id']).first())
    # t = np.asscalar(np.int16(ml_skill_to))
    # f = np.asscalar(np.int16(ml_skill_from))
    # pred_skill_to, pred_skill_from = db.session.query(Skill.skill_name).filter((Skill.skill_id==t)|(Skill.skill_id==f)).all()

    # print "PRED FROM",pred_skill_from
    # print "PRED TO",pred_skill_to
    return render_template("user_skill.html", user=new_user)


@app.route("/users/<int:user_id>")
def user_detail(user_id):
    """Show info about user."""

    user = User.query.get(user_id)

    skillto = db.session.query(Skill.skill_name).join(UserSkill).filter(UserSkill.skill_direction=='to', UserSkill.user_id==user_id).scalar()
    skillfrom = db.session.query(Skill.skill_name).join(UserSkill).filter(UserSkill.skill_direction=='from', UserSkill.user_id==user_id).scalar()

    ml_skill_to,ml_skill_from = ml.predict(db.session.query(User.user_occupation_id).filter(User.user_id==session['user_id']).first())
    t = np.asscalar(np.int16(ml_skill_to))
    f = np.asscalar(np.int16(ml_skill_from))
    pred_skill_to, pred_skill_from = db.session.query(Skill.skill_name).filter((Skill.skill_id==t)|(Skill.skill_id==f)).all()

    print "PRED FROM",pred_skill_from
    print "PRED TO",pred_skill_to
    return render_template("user_profile.html", user=user, map_key_api=map_key, skill_from=skillfrom, skill_to=skillto,
        pred_skill_to=pred_skill_to[0],pred_skill_from=pred_skill_from[0])




@app.route('/network_graph.json')
def network_data():
    """JSON information about ."""
    network.add_nodes(network.nodes)
    network.add_edges(network.skill_to, network.skill_from)

    graph_data = network.json_my_net_data(network.Z)
    return jsonify(graph_data)



@app.route('/simple_cycle.json/<int:user_id>')
def cycle_data(user_id):
    """JSON information about ."""
  
    # info for the smaller closed loop graph
    network.B.clear()
    lp = network.find_loop(network.Z, user_id)
    print lp
    if lp != "Loop Not Found":
        ed = network.generate_loop_edges(lp)
        network.add_attributes(network.B, lp, ed)
    else:
        print "FIND OTHER"
        # network.find_ngbrs(network.B,network.Z,user_id)
        lp = network.find_other(network.Z, user_id)
        
        if lp == "Path Not Found":
            message = "Path Not Found"
            print message
            return message
        ed = network.generate_edges(lp)
        network.add_attributes(network.B, lp, ed)

    print network.B.edges(data=True)
    print network.B.nodes(data=True)

    print "BEFORE USER GRAPH DATA LOOP DATA"

    user_graph_data = network.json_my_smallnet_data(network.B)
    print user_graph_data
    return jsonify(user_graph_data)

@app.route('/ngbrs_data.json/<int:user_id>')
def ngbrs_data(user_id):
    """JSON information about ."""
  
    # info for the ngbrs loop graph
    network.C.clear()
    network.find_ngbrs(network.C,network.Z,user_id)
  
    print "BEFORE USER GRAPH DATA NGBRS DATA"

    ngbrs_graph_data = network.json_my_smallnet_data(network.C)
    print ngbrs_graph_data
    return jsonify(ngbrs_graph_data)


@app.route('/one_to_one.json/<int:user_id>')
def mutual_rel_data(user_id):
    """JSON information about ."""

    userer = UserSkill.query.filter_by(user_id=user_id).all()
    for line in userer:
        if line.direction_id==1:
            lineto = [line.skill_id, line.skill_direction,line.direction_id]
            print lineto
        linefrom=[line.skill_id, line.skill_direction,line.direction_id]
        print linefrom
        
        skillname = db.session.query(Skill.skill_name).filter(Skill.skill_id==linefrom[0]).all()
        print "SKILLNAME FROM",skillname
        sk = db.session.query(UserSkill.user_id).filter(UserSkill.skill_id==linefrom[0], UserSkill.skill_direction!=0).all()
        print "SK FROM",sk
        for s in sk:
            sb = db.session.query(UserSkill.user_id).filter(UserSkill.user_id==s[0],UserSkill.skill_id==lineto[0], UserSkill.skill_direction!=1).all()
        print sb





@app.route('/logout')
def log_out():

    del session['user_id']
    flash("logged out!")
    return redirect('/')

@app.route('/user_skill', methods=['POST'])
def user_skill():

    skill_name_to = request.form.get('skill-name-to')
    skill_name_from = request.form.get('skill-name-from')

    # user_insession = User.query.filter_by(user_email=session['username']).first()
    # user_id_insession = user_insession.user_id

    user_id_insession = session['user_id']

    skillz_to_eval = [(skill_name_to,'to',1), (skill_name_from, 'from',0)]

    # Adding skill to db
    for skill_name, direction, dir_id in skillz_to_eval:
        if not Skill.query.filter_by(skill_name=skill_name).all():
            new_skill = Skill(skill_name=skill_name)
            db.session.add(new_skill)
            db.session.commit()
       
        # skill = db.session.query(Skill.skill_name, Skill.skill_id).join(UserSkill).filter(
        #         Skill.skill_name==skill_name,
        #         UserSkill.skill_direction==direction).first()
        s_id = db.session.query(Skill.skill_id).filter(Skill.skill_name==skill_name).first()
    
        skill = UserSkill.query.filter_by(user_id=user_id_insession, skill_direction=direction, skill_id=s_id).scalar()
        
        if not skill:
            if dir_id==0:
                new_userskill = UserSkill(user_id=user_id_insession, 
                                  skill_id=s_id, skill_direction=direction,direction_id=dir_id)
            new_userskill = UserSkill(user_id=user_id_insession, 
                                  skill_id=s_id, skill_direction=direction,direction_id=dir_id)

            db.session.add(new_userskill)
            db.session.commit()
            
        UserSkill.query.filter_by(user_id=user_id_insession,skill_direction=direction,direction_id=dir_id).update(dict(skill_id=s_id))
        db.session.commit()

        #finding edges from the new user skills and adding to network
        ######
        # all user connections with skills
        st = UserSkill.query.filter_by(user_id=user_id_insession).all()
        for line in st:
            skillid ,direction = line.skill_id, line.skill_direction
            if direction == 'from':
                skillname = db.session.query(Skill.skill_name).filter(Skill.skill_id==skillid).all()
                print "SKILLNAME FROM"
                sk = db.session.query(UserSkill.user_id).filter(UserSkill.skill_id==skillid, UserSkill.skill_direction=='to').all()
                print "SK FROM",sk
                network.Z.add_edges_from([(user_id_insession,n[0],{'name':skillname[0][0]}) for n in sk if user_id_insession!=n[0]])

            skillname = db.session.query(Skill.skill_name).filter(Skill.skill_id==skillid).all()
            print "SKILLNAME TO"
            sk = db.session.query(UserSkill.user_id).filter(UserSkill.skill_id==skillid, UserSkill.skill_direction=='from').all()
            print "SK TO", sk
            network.Z.add_edges_from([(n[0],user_id_insession,{'name':skillname[0][0]}) for n in sk if user_id_insession!=n[0]])

        # if not skill:
        #     new_skill = Skill(skill_name=skill_name)
        #     db.session.add(new_skill)
        #     db.session.commit()
        #     skill = new_skill

        # new_userskill = UserSkill(user_id=user_id_insession, 
        #                           skill_id=skill.skill_id, skill_direction=direction)
        # db.session.add(new_userskill)
        # db.session.commit()
        flash("your skills have been added to our network")

    return redirect("/users/%s" % session['user_id'])

@app.route('/update_skill', methods=['POST'])
def update_skill():
    user_id_insession = session['user_id']
    skill_name_to = request.form.get('update-skill-name-to')
    skill_name_from = request.form.get('update-skill-name-from')

    skillz_to_eval = [(skill_name_to,'to',1), (skill_name_from, 'from',0)]
    for skill_name, direction, dir_id in skillz_to_eval:
        if not Skill.query.filter_by(skill_name=skill_name).all():
            new_skill = Skill(skill_name=skill_name)
            db.session.add(new_skill)
            db.session.commit()
        s_id = db.session.query(Skill.skill_id).filter(Skill.skill_name==skill_name).first()
        print "UPDATING ID", s_id
    
        skill = UserSkill.query.filter_by(user_id=user_id_insession, skill_direction=direction,direction_id=dir_id).scalar()
        print "LOOKING UP UPDATING SKILL",skill
        
        if not skill:
            print "IF NOT SKILL"
            if dir_id==0:
                new_userskill = UserSkill(user_id=user_id_insession, 
                                  skill_id=s_id, skill_direction=direction,direction_id=dir_id)
                db.session.add(new_userskill)
                db.session.commit()
            
            new_userskill = UserSkill(user_id=user_id_insession, 
                                  skill_id=s_id, skill_direction=direction,direction_id=dir_id)
            
            db.session.add(new_userskill)
            db.session.commit()

        print "STARTING TO REMOVE EDGES"

        if direction=='from':
            print "REMOVING OUT EDGES",network.Z.out_edges([user_id_insession], data=True)
            network.Z.remove_edges_from(network.Z.out_edges([user_id_insession], data=True))
        print "REMOVING IN EDGES",network.Z.in_edges([user_id_insession], data=True)      
        network.Z.remove_edges_from(network.Z.in_edges([user_id_insession], data=True)) 
        
        UserSkill.query.filter_by(user_id=user_id_insession,skill_direction=direction).update(dict(skill_id=s_id,direction_id=dir_id))
        db.session.commit()
        print "NEW USERSKILL UPDATED"

        st = UserSkill.query.filter_by(user_id=user_id_insession).all()
        for line in st:
            skillid ,direction = line.skill_id, line.skill_direction
            if direction == 'from':
                skillname = db.session.query(Skill.skill_name).filter(Skill.skill_id==skillid).all()
                print "SKILLNAME FROM"
                sk = db.session.query(UserSkill.user_id).filter(UserSkill.skill_id==skillid, UserSkill.skill_direction=='to').all()
                print "SK FROM",sk
                network.Z.add_edges_from([(user_id_insession,n[0],{'name':skillname[0][0]}) for n in sk if user_id_insession!=n[0]])

            skillname = db.session.query(Skill.skill_name).filter(Skill.skill_id==skillid).all()
            print "SKILLNAME TO"
            sk = db.session.query(UserSkill.user_id).filter(UserSkill.skill_id==skillid, UserSkill.skill_direction=='from').all()
            print "SK TO", sk
            network.Z.add_edges_from([(n[0],user_id_insession,{'name':skillname[0][0]}) for n in sk if user_id_insession!=n[0]])

        flash("your skills have been updated to our network")

    return redirect("/users/%s" % session['user_id'])





@app.route('/login', methods=['GET'])
def login_form():
    """Show login form."""
    return render_template("login_form.html")


@app.route('/login', methods=['POST'])
def login_process():
    """Process login."""

    # Get form variables
    email = request.form["email"]
    password = request.form["password"]

    user = User.query.filter_by(user_email=email).first()

    if not user:
        flash("No such user")
        return redirect("/register")

    if bcrypt.hashpw(password.encode('UTF_8'), user.user_password.encode('UTF_8')).decode() == user.user_password:
        flash("it Matches")
    else:
        flash("Incorrect password")
         

    session["user_id"] = user.user_id

    flash("Logged In")
    return redirect("/users/%s" % user.user_id)

@app.after_request
def add_header(r):
    """
    Add headers to both force latest.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r



####################

# if __name__ == "__main__":
#     connect_to_db(app)
#     DebugToolbarExtension(app)
#     app.run(host='0.0.0.0', debug=True)

    
    

    