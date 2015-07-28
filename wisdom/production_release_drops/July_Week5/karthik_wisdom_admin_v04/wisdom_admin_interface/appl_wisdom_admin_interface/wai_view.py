import datetime
from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.db import transaction
import psycopg2
from psycopg2.extensions import AsIs
import sys

from django.template import RequestContext
import socket

from django.db import connection

#from appl_wisdom_admin_interface.forms import NameForm

from django.core.context_processors import csrf

from django.core.mail import send_mail, EmailMessage

from django.template.loader import render_to_string

import random
from random import choice
from string import digits, letters

#Rutvik Codes
from django.template import Template, Context 
from django.template.loader import get_template
import vn_splunk_rest_create_userrole as splunk_api
import json

userName="admin"
userPassword="s0cr4t3s"
managementPort="8089"


#This function will show the login page
def wai_login(request):
	if 'userid' in request.session:
	 	del request.session["userid"]

	if request.method == 'POST':
		frmusname = request.POST.get("txtusname")
		frmuspwd = request.POST.get("txtuspwd")
                
		cursor = connection.cursor()

		cursor.execute("select admin_userid, admin_username, admin_emailid, admin_password, admin_usertype, admin_active from wisdom_meta_data.wisdom_users where admin_emailid = %s and admin_password = %s and admin_active = 'Y'", (frmusname, frmuspwd))
		usid = usname = usemail = ustype = ""
		userrow = cursor.fetchall()
	        for ussirow in userrow:
        	        usid = ussirow[0]
                	usname = ussirow[1]
	               	usemail = ussirow[2]
			ustype = ussirow[4]
                
		cursor.close()
	
		if usemail != "":
			frmsysdt = datetime.datetime.now()
			frmsysdt = str(frmsysdt)[:19]

			cursor = connection.cursor()
			cursor.execute("update wisdom_meta_data.wisdom_users set last_loggedin = %s where admin_emailid = %s and admin_password = %s", (frmsysdt, frmusname, frmuspwd))
			connection.commit()
			cursor.close()
			
			request.session["userid"] = usid
			request.session["username"] = usname
			request.session["useremail"] = usemail
			request.session["usertype"] = ustype
			
			clientid = venueid = ""
			clidetcur = connection.cursor()
			clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
			desc = clidetcur.description
			clidet = [
				dict(zip([col[0] for col in desc], row))
				for row in clidetcur.fetchall()
			]
			if 'clientid' in request.session:
				clientid = request.session["clientid"]
			for row in clidet:
				if clientid == "":
					clientid = row["pk_client"]
			clidetcur.close()
			
			vendetcur = connection.cursor()
			vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
			desc = vendetcur.description
			vendet = [
				dict(zip([col[0] for col in desc], row))
				for row in vendetcur.fetchall()
			]
			for row in vendet:
				if venueid == "":
					venueid = row["pk_venue"]
			vendetcur.close()
			
			request.session["clientid"] = clientid
			request.session["venueid"] = venueid
			
			pgcur = connection.cursor()
			pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc limit 1;", [usid])

			uspgvi = pgcur.fetchall()
			pgna = '/wai_mngvalmas/'

			for ussipgvi in uspgvi:
        	        	pgna = "/" + ussipgvi[0] + "/"
			
			pgcur.close()


			return HttpResponseRedirect(pgna)
		else:
			return render(request, 'wai_login.html', {"errmsg" : "Invalid username and password." })
	else:
		return render(request, 'wai_login.html', {"errmsg" : ""})

#This function will clear the user session
def wai_logout(request):
 	del request.session["userid"]
	del request.session["clientid"]
	del request.session["venueid"]
	return HttpResponseRedirect('/wai_login/')

def wai_forgot(request):
	if request.method == 'POST':
		strusname = request.POST.get("txtusname")

		cursor = connection.cursor()
		cursor.execute("select admin_userid, admin_username, admin_emailid, admin_password from wisdom_meta_data.wisdom_users where admin_emailid = %s and admin_active = 'Y'", [strusname])
		usid = usname = usemail = uspwd = ""
		userrow = cursor.fetchall()
		for ussirow in userrow:
        	        usid = ussirow[0]
                	usname = ussirow[1]
			usemail = ussirow[2]
			uspwd = ussirow[3]

		if usemail != "":
			frmfrom = 'no-reply@venuenext.com'
			subject = 'Request for forgot Password'
			html_content = 'Dear '+usname+'<br /><br />Greetings! you have recently requested to forgot your password.<br /><br />Your Password is: '+uspwd+'<br /><br />Thanks<br />Admin Team'
			msg = EmailMessage(subject, html_content, frmfrom, [usemail])
			msg.content_subtype = "html"  # Main content is now text/html
			msg.send()

			return HttpResponseRedirect("/wai_login/")
		else:
			return render(request, 'wai_forgot.html', {"errmsg" : "Username is not available. Please check or enter the correct username."})
	else:
		return render(request, 'wai_forgot.html', {"errmsg" : ""})

def wai_chgpwd(request):
	if 'userid' not in request.session:
		return HttpResponseRedirect('/wai_login/')
	else:
		usid = request.session.get("userid")
		usem = request.session.get("username")
		ustyp = request.session.get("usertype")
		if request.method == 'POST':
			newpwd = request.POST.get("txtnewpwd")
			strsysdt = datetime.datetime.now()
	                strsysdt = str(strsysdt)[:19]

			cursor = connection.cursor()
			cursor.execute("update wisdom_meta_data.wisdom_users set admin_password = %s, admin_updatedon = %s, admin_updatedby = %s where admin_userid = %s", (newpwd, strsysdt, usid, usid))
			connection.commit()
			cursor.close()

			return HttpResponseRedirect("/wai_chgpwd/")
		else:
			oldpwd = ''
			cursor = connection.cursor()
			cursor.execute("select admin_userid, admin_username, admin_emailid, admin_password from wisdom_meta_data.wisdom_users where admin_userid = %s", [usid])
			userrow = cursor.fetchall()
			for ussirow in userrow:
				oldpwd = ussirow[3]

			pgcur = connection.cursor()
			pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
		        desc = pgcur.description
       			pgdet = [
       				dict(zip([col[0] for col in desc], row))
	                	for row in pgcur.fetchall()
	       		        ]
		        pgcur.close()

			clientid = ""
			if 'clientid' in request.session:
				clientid = request.session["clientid"]

			clidetcur = connection.cursor()
			clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
			desc = clidetcur.description
			clidet = [
				dict(zip([col[0] for col in desc], row))
				for row in clidetcur.fetchall()
				]
			for row in clidet:
				if clientid == "":
					clientid = row["pk_client"]
			clidetcur.close()
			
			vendetcur = connection.cursor()
			vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
			desc = vendetcur.description
			vendet = [
				dict(zip([col[0] for col in desc], row))
				for row in vendetcur.fetchall()
			]
			vendetcur.close()

			return render(request, 'wai_chngpwd.html', {"errmsg" : "", 'op': oldpwd, 'hid': 6, 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet })

#Wisdom Admin interface for validation master ends
#This function will show all the records in the validation master table, also based on the project name and active status selection it will be filtered as well
def wai_mngvalmas(request):
	if 'userid' not in request.session:
		return HttpResponseRedirect('/wai_login/')
	else:
		usid = request.session.get("userid")
		usem = request.session.get("username")
		ustyp = request.session.get("usertype")

		ddlcursor = connection.cursor()
		ddlcursor.execute("SELECT project_id, project_name, scheduled_start_time, number_of_jobs, latest_run_date, latest_run_duration_minutes, average_run_duration_minutes, created_at, modified_at, created_by, modified_by, report_timezone_scheduled_time, validation_wrapper_summary_time, pk_client, pk_venue, postgres_to_redshift_process FROM wisdom_meta_data.wisdom_jobproject order by project_id asc")

	        desc = ddlcursor.description
       		projdet = [
       			dict(zip([col[0] for col in desc], row))
	                for row in ddlcursor.fetchall()
       		        ]
	        ddlcursor.close()
		projid = strprity = actsta = intpgcnt = strProjDet = strActDet = strPrioDet = ""

		strsortby = "DESC"
		strsortna = "id"

		if 'pid' in request.GET:
			projid = request.GET.get('pid')
			cursor = connection.cursor()
			if projid != "":
        			cursor.execute("SELECT wp.project_name, vm.id, vm.code, vm.description, vm.associated_entity, vm.category, vm.threshold_value, vm.status, vm.created_on, vm.updated_on, vm.created_by, vm.updated_by, vm.project_id, vm.priority, vm.active_flag, vm.pk_client, vm.pk_venue, vm.validation_query FROM validation.wisdom_data_validation_master vm, wisdom_meta_data.wisdom_jobproject wp where wp.project_id = vm.project_id and vm.project_id = %s order by id desc", [projid])
			else:
				cursor.execute("SELECT wp.project_name, vm.id, vm.code, vm.description, vm.associated_entity, vm.category, vm.threshold_value, vm.status, vm.created_on, vm.updated_on, vm.created_by, vm.updated_by, vm.project_id, vm.priority, vm.active_flag, vm.pk_client, vm.pk_venue, vm.validation_query FROM validation.wisdom_data_validation_master vm, wisdom_meta_data.wisdom_jobproject wp where wp.project_id = vm.project_id order by id desc")
	
               		desc = cursor.description
	                valmasfuldet = [
       		                dict(zip([col[0] for col in desc], row))
               		        for row in cursor.fetchall()
                       		]
	                cursor.close()
		else:
			if request.method == 'POST':
				projid = request.POST.get("ddlproject")
				actsta = request.POST.get("ddlactive")
				strprity = request.POST.get("ddlpriority")
				
				cursor = connection.cursor()

				if projid != "":
					strProjDet = "and vm.project_id = "+ projid
				if actsta != "":
					strActDet = "and vm.active_flag = '" + actsta + "'"
				if strprity != "":
					strPrioDet = "and vm.priority = " + strprity
				
				cursor.execute("SELECT wp.project_name, vm.id, vm.code, vm.description, vm.associated_entity, vm.category, vm.threshold_value, vm.status, vm.created_on, vm.updated_on, vm.created_by, vm.updated_by, vm.project_id, vm.priority, vm.active_flag, vm.pk_client, vm.pk_venue, vm.validation_query FROM validation.wisdom_data_validation_master vm, wisdom_meta_data.wisdom_jobproject wp where wp.project_id = vm.project_id %(prjids)s %(actflg)s %(proi)s order by id desc limit 50", { 'prjids': AsIs(strProjDet), 'actflg': AsIs(strActDet), 'proi': AsIs(strPrioDet) })

	               		desc = cursor.description
		                valmasfuldet = [
       			                dict(zip([col[0] for col in desc], row))
               			        for row in cursor.fetchall()
                       			]
		                cursor.close()

				pgcntcur = connection.cursor()		
				pgcntcur.execute("SELECT count(*) as pagecounts FROM validation.wisdom_data_validation_master vm, wisdom_meta_data.wisdom_jobproject wp where wp.project_id = vm.project_id %(prjids)s %(actflg)s %(proi)s", { 'prjids': AsIs(strProjDet), 'actflg': AsIs(strActDet), 'proi': AsIs(strPrioDet) })				
				dspgCnt = pgcntcur.fetchall()
			
				for pgcntsi in dspgCnt:
					intpgcnt = pgcntsi[0]
				
				if intpgcnt is None:
					intpgcnt = 0

				pgcntcur.close()
	
			else:
				stlimt = 0
				cursor = connection.cursor()
			        cursor.execute("SELECT wp.project_name, vm.id, vm.code, vm.description, vm.associated_entity, vm.category, vm.threshold_value, vm.status, vm.created_on, vm.updated_on, vm.created_by, vm.updated_by, vm.project_id, vm.priority, vm.active_flag, vm.pk_client, vm.pk_venue, vm.validation_query FROM validation.wisdom_data_validation_master vm, wisdom_meta_data.wisdom_jobproject wp where wp.project_id = vm.project_id order by id desc limit 50 offset %s", [stlimt])
				desc = cursor.description
       				valmasfuldet = [
					dict(zip([col[0] for col in desc], row))
				        for row in cursor.fetchall()
					]
				cursor.close()			

				pgcntcur = connection.cursor()
			        pgcntcur.execute("SELECT count(*) as pagecounts FROM validation.wisdom_data_validation_master vm, wisdom_meta_data.wisdom_jobproject wp where wp.project_id = vm.project_id")
				dspgCnt = pgcntcur.fetchall()
			
				for pgcntsi in dspgCnt:
					intpgcnt = pgcntsi[0]
				
				if intpgcnt is None:
					intpgcnt = 0

				pgcntcur.close()

		pgcur = connection.cursor()
		pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
		desc = pgcur.description
       		pgdet = [
       			dict(zip([col[0] for col in desc], row))
		       	for row in pgcur.fetchall()
			]
		pgcur.close()

		clientid = ""
		if 'clientid' in request.session:
			clientid = request.session["clientid"]

		clidetcur = connection.cursor()
		clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
		desc = clidetcur.description
		clidet = [
			dict(zip([col[0] for col in desc], row))
			for row in clidetcur.fetchall()
			]
		for row in clidet:
			if clientid == "":
				clientid = row["pk_client"]
		
		clidetcur.close()

		vendetcur = connection.cursor()
		vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
		desc = vendetcur.description
		vendet = [
			dict(zip([col[0] for col in desc], row))
			for row in vendetcur.fetchall()
		]
		vendetcur.close()

		return render(request, "wai_validation_master.html", {'valmasdet': valmasfuldet, 'projdet': projdet, 'projid': projid, 'actsta': actsta, 'hid': "1", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'ddlprio': strprity, 'pgcntsi': intpgcnt, 'pgid': 1, 'sortby': strsortby, 'sortna': strsortna, 'clidet': clidet, 'vendet': vendet })

def wai_mngpgvalmas(request):
	if 'userid' not in request.session:
		return HttpResponseRedirect('/wai_login/')
	else:
		usid = request.session.get("userid")
		usem = request.session.get("username")
		ustyp = request.session.get("usertype")

		ddlcursor = connection.cursor()
		ddlcursor.execute("SELECT project_id, project_name, scheduled_start_time, number_of_jobs, latest_run_date, latest_run_duration_minutes, average_run_duration_minutes, created_at, modified_at, created_by, modified_by, report_timezone_scheduled_time, validation_wrapper_summary_time, pk_client, pk_venue, postgres_to_redshift_process FROM wisdom_meta_data.wisdom_jobproject order by project_id asc")

	        desc = ddlcursor.description
       		projdet = [
       			dict(zip([col[0] for col in desc], row))
	                for row in ddlcursor.fetchall()
       		        ]
	        ddlcursor.close()
		
		strsortby = "DESC"
		strsortna = "id"
		
		if request.method == 'POST':	
			projid = strprity = actsta = intpgcnt = strProjDet = strActDet = strPrioDet = ""
			projid = request.POST.get("hidProjId")
			actsta = request.POST.get("hidActSta")
			strprity = request.POST.get("hidPriori")
			intpagid = request.POST.get("hidPagId")
			strsortby = request.POST.get("hidPgOrdBy")
			strsortna = request.POST.get("hidPgOrdNa")
				
			cursor = connection.cursor()

			if intpagid == 1:
				startlimit = 0
			else:
				startlimit = int(intpagid) - 1
				startlimit = 50 * int(startlimit)

			if projid != "":
				strProjDet = "and vm.project_id = "+ projid
			if actsta != "":
				strActDet = "and vm.active_flag = '" + actsta + "'"
			if strprity != "":
				strPrioDet = "and vm.priority = " + strprity

			cursor.execute("SELECT wp.project_name, vm.id, vm.code, vm.description, vm.associated_entity, vm.category, vm.threshold_value, vm.status, vm.created_on, vm.updated_on, vm.created_by, vm.updated_by, vm.project_id, vm.priority, vm.active_flag, vm.pk_client, vm.pk_venue, vm.validation_query FROM validation.wisdom_data_validation_master vm, wisdom_meta_data.wisdom_jobproject wp where wp.project_id = vm.project_id %(prjids)s %(actflg)s %(proi)s order by %(ordna)s %(ordby)s limit 50 OFFSET %(limst)s", { 'prjids': AsIs(strProjDet), 'actflg': AsIs(strActDet), 'proi': AsIs(strPrioDet), 'ordna': AsIs(strsortna), 'ordby': AsIs(strsortby), 'limst': AsIs(startlimit) })
			desc = cursor.description
			valmasfuldet = [
				dict(zip([col[0] for col in desc], row))
				for row in cursor.fetchall()
				]
			cursor.close()	
		
			pgcntcur = connection.cursor()
			pgcntcur.execute("SELECT count(*) as pagecounts FROM validation.wisdom_data_validation_master vm, wisdom_meta_data.wisdom_jobproject wp where wp.project_id = vm.project_id %(prjids)s %(actflg)s %(proi)s", { 'prjids': AsIs(strProjDet), 'actflg': AsIs(strActDet), 'proi': AsIs(strPrioDet) })
			dspgCnt = pgcntcur.fetchall()
			
			for pgcntsi in dspgCnt:
				intpgcnt = pgcntsi[0]
				
			if intpgcnt is None:
				intpgcnt = 0

			pgcntcur.close()
	
			pgcur = connection.cursor()
			pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
			desc = pgcur.description
       			pgdet = [
       				dict(zip([col[0] for col in desc], row))
		       		for row in pgcur.fetchall()
				]
			pgcur.close()

			clientid = ""
			if 'clientid' in request.session:
				clientid = request.session["clientid"]

			clidetcur = connection.cursor()
			clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
			desc = clidetcur.description
			clidet = [
				dict(zip([col[0] for col in desc], row))
				for row in clidetcur.fetchall()
				]
			for row in clidet:
				if clientid == "":
					clientid = row["pk_client"]
		
			clidetcur.close()

			vendetcur = connection.cursor()
			vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
			desc = vendetcur.description
			vendet = [
				dict(zip([col[0] for col in desc], row))
				for row in vendetcur.fetchall()
			]
			vendetcur.close()

			return render(request, "wai_validation_master.html", {'valmasdet': valmasfuldet, 'projdet': projdet, 'projid': projid, 'actsta': actsta, 'hid': "1", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'ddlprio': strprity, 'pgcntsi': intpgcnt, 'pgid': intpagid, 'sortby': strsortby, 'sortna': strsortna, 'clidet': clidet, 'vendet': vendet })
		else:
			return HttpResponseRedirect("/wai_mngvalmas/")


def wai_valmasidgen(request):
	if request.POST.has_key('hidcrtvalmasprjid'):
		pid = request.POST['hidcrtvalmasprjid']
		cursor = connection.cursor()
		cursor.execute("SELECT (max(id)+1) as id from validation.wisdom_data_validation_master where project_id = %s", [pid])
		masrow = cursor.fetchall()
		masid = ""
		for massing in masrow:
			masid = massing[0]
		
		if masid is None:
			masid = int(pid) + 1
		
		return HttpResponse(masid)

#This function will open form to insert a new record in validation master table
def createvalmas(request):
	usid = request.session.get("userid")
	usem = request.session.get("username")
	ustyp = request.session.get("usertype")

	if request.method == 'POST':
		frmmprojid = request.POST.get("txtprojid")
                frmmid = request.POST.get("txtmasid")
                frmmcode = "Null" #request.POST.get("txtcode")
		frmmdesc = request.POST.get("txtdesc")
                frmmassenty = request.POST.get("txtassoenty")
                frmmcate = "Null" #request.POST.get("txtcate")
                frmmtherval = request.POST.get("txtthersval")
                frmmstatus = request.POST.get("txtstatus")
                frmmpriority = request.POST.get("txtpriority")
                frmmactflag = request.POST.get("txtactflag")
                frmmvalquery = request.POST.get("txtvalqry")
		frmsysdt = datetime.datetime.now()
                frmsysdt = str(frmsysdt)[:19]

		strclient = 1
		strvenue = 1

		getvidcur = connection.cursor()
		getvidcur.execute("SELECT (max(id)+1) as id from validation.wisdom_data_validation_master where project_id = %s", [frmmprojid])
		masrow = getvidcur.fetchall()
		frmmid = ""
		for massing in masrow:
			frmmid = massing[0]
		
		if frmmid is None:
			frmmid = int(frmmprojid) + 1
		getvidcur.close()

                cursor = connection.cursor()
                cursor.execute("insert into validation.wisdom_data_validation_master (id, code, description, associated_entity, category, threshold_value, status, project_id, priority, active_flag, validation_query, created_on, pk_client, pk_venue, created_by) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (frmmid, frmmcode, frmmdesc, frmmassenty, frmmcate, frmmtherval, frmmstatus, frmmprojid, frmmpriority, frmmactflag, frmmvalquery, frmsysdt, strclient, strvenue, usem))
                connection.commit()
                cursor.close()

		strRedirect = '/wai_mngvalmas/?pid=' + frmmprojid
		return HttpResponseRedirect(strRedirect)
	else:
		if 'pid' not in request.GET:
			return HttpResponseRedirect('/wai_mngvalmas/')
		else:
			pid = request.GET.get("pid")
			ddlcursor = connection.cursor()
        		ddlcursor.execute("SELECT project_id, project_name, scheduled_start_time, number_of_jobs, latest_run_date, latest_run_duration_minutes, average_run_duration_minutes, created_at, modified_at, created_by, modified_by, report_timezone_scheduled_time, validation_wrapper_summary_time, pk_client, pk_venue, postgres_to_redshift_process FROM wisdom_meta_data.wisdom_jobproject order by project_id asc")

		        desc = ddlcursor.description
        		projdet = [
                		dict(zip([col[0] for col in desc], row))
	                	for row in ddlcursor.fetchall()
	        	        ]
		        ddlcursor.close()
	
        		valfuldet = masid = ""
		        valmasid = request.GET.get("mid")
        		if pid != "":
				validcur = connection.cursor()
		        	validcur.execute("SELECT (max(id)+1) as id from validation.wisdom_data_validation_master where project_id = %s", [pid])

			        masrow = validcur.fetchall()
        			for massing in masrow:
					masid = massing[0]
	
				if masid is None:
					masid = int(pid) + 1
	
				validcur.close()
			else:
				masid = ""

			pgcur = connection.cursor()
			pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
			desc = pgcur.description
		       	pgdet = [
       				dict(zip([col[0] for col in desc], row))
	       			for row in pgcur.fetchall()
				]
			pgcur.close()

			clientid = ""
			if 'clientid' in request.session:
				clientid = request.session["clientid"]

			clidetcur = connection.cursor()
			clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
			desc = clidetcur.description
			clidet = [
				dict(zip([col[0] for col in desc], row))
				for row in clidetcur.fetchall()
				]
			for row in clidet:
				if clientid == "":
					clientid = row["pk_client"]
			clidetcur.close()
			
			vendetcur = connection.cursor()
			vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
			desc = vendetcur.description
			vendet = [
				dict(zip([col[0] for col in desc], row))
				for row in vendetcur.fetchall()
			]
			vendetcur.close()
 
			return render(request, 'wai_crtvalmas.html', {'mid': masid, 'projdet': projdet, 'projid': pid, 'hid': "1", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet })
			

#This function insert a new record in validation master table
def insvalmas(request):
        if request.method == 'POST':
		usid = request.session.get("userid")
		usem = request.session.get("username")
		ustyp = request.session.get("usertype")

		frmmprojid = request.POST.get("txtprojid")
                frmmid = request.POST.get("txtmasid")
                frmmcode = "Null" #request.POST.get("txtcode")
		frmmdesc = request.POST.get("txtdesc")
                frmmassenty = request.POST.get("txtassoenty")
                frmmcate = "Null" #request.POST.get("txtcate")
                frmmtherval = request.POST.get("txtthersval")
                frmmstatus = request.POST.get("txtstatus")
                frmmpriority = request.POST.get("txtpriority")
                frmmactflag = request.POST.get("txtactflag")
                frmmvalquery = request.POST.get("txtvalqry")
		frmsysdt = datetime.datetime.now()
                frmsysdt = str(frmsysdt)[:19]
		strclient = 1
		strvenue = 1

                cursor = connection.cursor()

                cursor.execute("insert into validation.wisdom_data_validation_master (id, code, description, associated_entity, category, threshold_value, status, project_id, priority, active_flag, validation_query, created_on, pk_client, pk_venue) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (frmmid, frmmcode, frmmdesc, frmmassenty, frmmcate, frmmtherval, frmmstatus, frmmprojid, frmmpriority, frmmactflag, frmmvalquery, frmsysdt, strclient, strvenue))
                connection.commit()
                cursor.close()

		return HttpResponseRedirect('/wai_mngvalmas/')


#This function will show the edit/update form for validation master table
def viewdat(request):
	usid = request.session.get("userid")
	usem = request.session.get("username")
	ustyp = request.session.get("usertype")

	ddlcursor = connection.cursor()
        ddlcursor.execute("SELECT project_id, project_name, scheduled_start_time, number_of_jobs, latest_run_date, latest_run_duration_minutes, average_run_duration_minutes, created_at, modified_at, created_by, modified_by, report_timezone_scheduled_time, validation_wrapper_summary_time, pk_client, pk_venue, postgres_to_redshift_process FROM wisdom_meta_data.wisdom_jobproject order by project_id asc")

        desc = ddlcursor.description
        projdet = [
                dict(zip([col[0] for col in desc], row))
                for row in ddlcursor.fetchall()
                ]
        ddlcursor.close()

        valfuldet = ""
        valmasid = request.GET.get("mid")
        cursor = connection.cursor()

        cursor.execute("SELECT vm.id, vm.code, vm.description, vm.associated_entity, vm.category, vm.threshold_value, vm.status, vm.project_id, vm.priority, vm.active_flag, vm.validation_query, wp.project_name FROM validation.wisdom_data_validation_master vm, wisdom_meta_data.wisdom_jobproject wp where wp.project_id = vm.project_id and vm.id = %s", [valmasid])

        masrow = cursor.fetchall()
        for massing in masrow:
                masid = massing[0]
                mascode = massing[1]
                masdesc = massing[2]
                masassenty = massing[3]
                mascate = massing[4]
                masther = massing[5]
                masstatus = massing[6]
                masprojid = massing[7]
                maspriori = massing[8]
                masactflag = massing[9]
                masvalquer = massing[10]
		masprojname = massing[11]

	pgcur = connection.cursor()
	pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
	desc = pgcur.description
       	pgdet = [
		dict(zip([col[0] for col in desc], row))
	       	for row in pgcur.fetchall()
		]
	pgcur.close()

        return render(request, 'wai_editvalmas.html', {'mid': masid, 'mcode': mascode, 'mdesc': masdesc, 'masentity': masassenty, 'mcate' : mascate, 'mthsoval': masther, 'mstatus': masstatus, 'mprojectid': masprojid, 'mpriority': maspriori, 'mactflag': masactflag, 'mvalquery': masvalquer, 'projdet': projdet, 'mprojname': masprojname, 'hid': "1", 'ustyp': ustyp, 'pgdet': pgdet })

#This function will execute, updating the record in validation master table
def editvalmas(request):
	if request.method == 'POST':
	        arrprojid = request.POST.getlist('hidsiprojid')
		arrvalmasid = request.POST.getlist('hidvalid')
		arrvaldesc =  request.POST.getlist('txtsidesc')
		arrassenty =  request.POST.getlist('txtassent')
		arrtherval =  request.POST.getlist('txttherval')
		arrpriority =  request.POST.getlist('txtprioriy')
		arractflag =  request.POST.getlist('txtactfl')
		arrvalquery =  request.POST.getlist('txtsivalqry')
		usid = request.session.get("userid")
		usem = request.session.get("username")
		ustyp = request.session.get("usertype")

		i = 0

		frmsysdt = datetime.datetime.now()
		frmsysdt = str(frmsysdt)[:19]
		while i < len(arrprojid):
			frmmprojid = arrprojid[i]
		        frmmid = arrvalmasid[i]
			frmmdesc = arrvaldesc[i]
	        	frmmassenty = arrassenty[i]
	        	frmmtherval = arrtherval[i]
		        frmmpriority = arrpriority[i]
        		frmmactflag = arractflag[i]
			frmmvalquery = arrvalquery[i]
			
			cursor = connection.cursor()
			cursor.execute("update validation.wisdom_data_validation_master set description = %s, associated_entity = %s, threshold_value = %s, project_id = %s, priority = %s, active_flag = %s, validation_query = %s, updated_on = %s, updated_by = %s where id = %s", (frmmdesc, frmmassenty, frmmtherval, frmmprojid, frmmpriority, frmmactflag, frmmvalquery, frmsysdt, usem, frmmid))
			connection.commit()
        		cursor.close()
			i = i + 1

		ddlcursor = connection.cursor()
		ddlcursor.execute("SELECT project_id, project_name, scheduled_start_time, number_of_jobs, latest_run_date, latest_run_duration_minutes, average_run_duration_minutes, created_at, modified_at, created_by, modified_by, report_timezone_scheduled_time, validation_wrapper_summary_time, pk_client, pk_venue, postgres_to_redshift_process FROM wisdom_meta_data.wisdom_jobproject order by project_id asc")

	        desc = ddlcursor.description
       		projdet = [
       			dict(zip([col[0] for col in desc], row))
	                for row in ddlcursor.fetchall()
       		        ]
	        ddlcursor.close()

		pgcur = connection.cursor()
		pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
		desc = pgcur.description
       		pgdet = [
       			dict(zip([col[0] for col in desc], row))
	        	for row in pgcur.fetchall()
	       	        ]
		pgcur.close()

		projid = strprity = actsta = intpgcnt = strProjDet = strActDet = strPrioDet = strsortby = strsortna = ""
		
		projid = request.POST.get("hidedprjid")
		actsta = request.POST.get("hidedactsta")
		strprity = request.POST.get("hidedprio")
		strsortby = request.POST.get("hidEdOrdBy")
		strsortna = request.POST.get("hidEdOrdNa")
		
		startlimit = 0

		intpagid = request.POST.get("hidEdPagId")
							
		if intpagid == 1:
			startlimit = 0
		else:
			startlimit = int(intpagid) - 1
			startlimit = 50 * int(startlimit)
	
		cursor = connection.cursor()

		if projid != "":
			strProjDet = "and vm.project_id = "+ projid
		if actsta != "":
			strActDet = "and vm.active_flag = '" + actsta + "'"
		if strprity != "":
			strPrioDet = "and vm.priority = " + strprity

		cursor.execute("SELECT wp.project_name, vm.id, vm.code, vm.description, vm.associated_entity, vm.category, vm.threshold_value, vm.status, vm.created_on, vm.updated_on, vm.created_by, vm.updated_by, vm.project_id, vm.priority, vm.active_flag, vm.pk_client, vm.pk_venue, vm.validation_query FROM validation.wisdom_data_validation_master vm, wisdom_meta_data.wisdom_jobproject wp where wp.project_id = vm.project_id %(prjids)s %(actflg)s %(proi)s order by %(ordna)s %(ordby)s limit 50 OFFSET %(limst)s", { 'prjids': AsIs(strProjDet), 'actflg': AsIs(strActDet), 'proi': AsIs(strPrioDet), 'ordna': AsIs(strsortna), 'ordby': AsIs(strsortby), 'limst': AsIs(startlimit) })
		desc = cursor.description
		valmasfuldet = [
       			dict(zip([col[0] for col in desc], row))
		        for row in cursor.fetchall()
            		]
		cursor.close()
		
		pgcntcur = connection.cursor()
		pgcntcur.execute("SELECT count(*) as pagecounts FROM validation.wisdom_data_validation_master vm, wisdom_meta_data.wisdom_jobproject wp where wp.project_id = vm.project_id %(prjids)s %(actflg)s %(proi)s", { 'prjids': AsIs(strProjDet), 'actflg': AsIs(strActDet), 'proi': AsIs(strPrioDet) })
		dspgCnt = pgcntcur.fetchall()
		for pgcntsi in dspgCnt:
			intpgcnt = pgcntsi[0]
				
		if intpgcnt is None:
			intpgcnt = 0

		pgcntcur.close()
	
		pgcur = connection.cursor()
		pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
		desc = pgcur.description
	       	pgdet = [
       			dict(zip([col[0] for col in desc], row))
			for row in pgcur.fetchall()
			]
		pgcur.close()

		clientid = ""
		if 'clientid' in request.session:
			clientid = request.session["clientid"]

		clidetcur = connection.cursor()
		clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
		desc = clidetcur.description
		clidet = [
			dict(zip([col[0] for col in desc], row))
			for row in clidetcur.fetchall()
			]
		for row in clidet:
			if clientid == "":
				clientid = row["pk_client"]
		clidetcur.close()
			
		vendetcur = connection.cursor()
		vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
		desc = vendetcur.description
		vendet = [
			dict(zip([col[0] for col in desc], row))
			for row in vendetcur.fetchall()
		]
		vendetcur.close()

		return render(request, "wai_validation_master.html", {'valmasdet': valmasfuldet, 'projdet': projdet, 'projid': projid, 'actsta': actsta, 'hid': "1", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'ddlprio': strprity, 'pgcntsi': intpgcnt, 'pgid': intpagid, 'sortby': strsortby, 'sortna': strsortna, 'clidet': clidet, 'vendet': vendet })
	else:
		return HttpResponseRedirect('/wai_mngvalmas/')


#This function will delete a particular record with the given id in validation master table.
def delmasdat(request):
        valmasid = request.GET.get("mid")
        cursor = connection.cursor()
        cursor.execute("delete FROM validation.wisdom_data_validation_master where id in (%s)", [valmasid])
        connection.commit()
        cursor.close()
        return render(request, 'story/thanks.html', {'succmsg': "Validation master detail deleted successfully", 'hid': "1" })

#Wisdom Admin interface for validation master ends


#Manage project/Job Starts
def wai_mngprojob(request):
	if 'userid' not in request.session:
		return HttpResponseRedirect('/wai_login/')
	else:
		jobdet = ""
		usid = request.session.get("userid")
		usem = request.session.get("username")
		ustyp = request.session.get("usertype")

		pgcur = connection.cursor()
		pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
		desc = pgcur.description
	       	pgdet = [
			dict(zip([col[0] for col in desc], row))
	       		for row in pgcur.fetchall()
			]
		pgcur.close()

		projid = request.GET.get("pid")
		if 'pid' in request.GET:
			if request.GET.get('pid') != "":
				ddlcursor = connection.cursor()
				#ddlcursor.execute("select jm.job_id, jm.job_name, jm.job_description, jm.project_id, jm.frequency, jm.category, jm.incremental_baseline_date_start, jm.incremental_baseline_date_end, jm.active, jm.is_high_frequency_job, jm.success_email_threshold, jm.success_email_counter, jm.pk_client, jm.pk_venue, jm.createddate, jm.createdby, wp.project_name from wisdom_meta_data.wisdom_jobmaster jm, wisdom_meta_data.wisdom_jobproject wp where wp.project_id = jm.project_id and jm.project_id = %s", [projid])
				ddlcursor.execute("SELECT project_id, project_name, scheduled_start_time, number_of_jobs, latest_run_date, latest_run_duration_minutes, average_run_duration_minutes, created_at, modified_at, created_by, modified_by, report_timezone_scheduled_time, validation_wrapper_summary_time, pk_client, pk_venue, postgres_to_redshift_process FROM wisdom_meta_data.wisdom_jobproject where project_id = %s order by project_id asc", [projid])
				projrow = ddlcursor.fetchall()

				projname = projschestdt = projnojobs = projlastrundt = projlastrundur = projavgrundur = projreptzstdt = projposts3 = ""
	
			        for projsing in projrow:
					projid = projsing[0]
					projname = projsing[1]
					projschestdt = projsing[2]
					projnojobs = projsing[3]
					projlastrundt = projsing[4]
					projlastrundur = projsing[5]
					projavgrundur = projsing[12]
					projreptzstdt = projsing[11]
					projposts3 = projsing[15]
	
			        ddlcursor.close()
	
				jobcursor = connection.cursor()
				jobcursor.execute("select jm.job_id, jm.job_name, jm.job_description, jm.project_id, jm.frequency, jm.category, jm.incremental_baseline_date_start, jm.incremental_baseline_date_end, jm.active, jm.is_high_frequency_job, jm.success_email_threshold, jm.success_email_counter, jm.pk_client, jm.pk_venue, jm.createddate, jm.createdby, wp.project_name from wisdom_meta_data.wisdom_jobmaster jm, wisdom_meta_data.wisdom_jobproject wp where wp.project_id = jm.project_id and jm.project_id = %s order by job_id asc", [projid])
		        	desc = jobcursor.description
	        		jobdet = [
        	        		dict(zip([col[0] for col in desc], row))
	        	        	for row in jobcursor.fetchall()
	        		        ]
			        jobcursor.close()

				clientid = ""
				if 'clientid' in request.session:
					clientid = request.session["clientid"]

				clidetcur = connection.cursor()
				clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
				desc = clidetcur.description
				clidet = [
					dict(zip([col[0] for col in desc], row))
					for row in clidetcur.fetchall()
				]

				for row in clidet:
					if clientid == "":
						clientid = row["pk_client"]
				clidetcur.close()
			
				vendetcur = connection.cursor()
				vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
				desc = vendetcur.description
				vendet = [
					dict(zip([col[0] for col in desc], row))
					for row in vendetcur.fetchall()
					]
				vendetcur.close()

				return render(request, 'wai_projobdet.html', {'projid': projid, 'projname': projname, 'projschestdt': projschestdt, 'projnojobs': projnojobs, 'projlastrundt': projlastrundt, 'projlastrundur': projlastrundur, 'projavgrundur': projavgrundur, 'projreptzstdt': projreptzstdt, 'projposts3': projposts3, 'hid': "2", 'usna': usem, 'jobdet': jobdet, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet })
			else:
				ddlcursor = connection.cursor()
				ddlcursor.execute("SELECT project_id, project_name, scheduled_start_time, number_of_jobs, latest_run_date, latest_run_duration_minutes, average_run_duration_minutes, created_at, modified_at, created_by, modified_by, report_timezone_scheduled_time, validation_wrapper_summary_time, pk_client, pk_venue, postgres_to_redshift_process FROM wisdom_meta_data.wisdom_jobproject order by project_id asc")
			        desc = ddlcursor.description
	        		projdet = [
	               			dict(zip([col[0] for col in desc], row))
	                		for row in ddlcursor.fetchall()
	        		        ]
			        ddlcursor.close()

				clientid = ""
				if 'clientid' in request.session:
					clientid = request.session["clientid"]

				clidetcur = connection.cursor()
				clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
				desc = clidetcur.description
				clidet = [
					dict(zip([col[0] for col in desc], row))
					for row in clidetcur.fetchall()
				]

				for row in clidet:
					if clientid == "":
						clientid = row["pk_client"]
				clidetcur.close()
			
				vendetcur = connection.cursor()
				vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
				desc = vendetcur.description
				vendet = [
					dict(zip([col[0] for col in desc], row))
					for row in vendetcur.fetchall()
				]
				vendetcur.close()

				return render(request, 'wai_projob.html', {'projdet': projdet, 'hid': "2", 'usna': usem, 'jobdet': jobdet, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet })
		else:
			ddlcursor = connection.cursor()
			ddlcursor.execute("SELECT project_id, project_name, scheduled_start_time, number_of_jobs, latest_run_date, latest_run_duration_minutes, average_run_duration_minutes, created_at, modified_at, created_by, modified_by, report_timezone_scheduled_time, validation_wrapper_summary_time, pk_client, pk_venue, postgres_to_redshift_process FROM wisdom_meta_data.wisdom_jobproject order by project_id asc")
		        desc = ddlcursor.description
        		projdet = [
                		dict(zip([col[0] for col in desc], row))
	                	for row in ddlcursor.fetchall()
	        	        ]
		        ddlcursor.close()
			
			clientid = ""
			if 'clientid' in request.session:
				clientid = request.session["clientid"]

			clidetcur = connection.cursor()
			clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
			desc = clidetcur.description
			clidet = [
				dict(zip([col[0] for col in desc], row))
				for row in clidetcur.fetchall()
				]
			for row in clidet:
				if clientid == "":
					clientid = row["pk_client"]
			clidetcur.close()
			
			vendetcur = connection.cursor()
			vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
			desc = vendetcur.description
			vendet = [
				dict(zip([col[0] for col in desc], row))
				for row in vendetcur.fetchall()
			]
			vendetcur.close()			

			return render(request, 'wai_projob.html', {'projdet': projdet, 'hid': "2", 'usna': usem, 'jobdet': jobdet, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet })

#Function to upadte the records to table "wisdom_meta_data.wisdom_jobproject"
def wai_upprojdets(request):
	if request.method == 'POST':
		usid = request.session.get("userid")
		usem = request.session.get("username")
		ustyp = request.session.get("usertype")

		arrprojid = request.POST.getlist('hidprojid')
		arrprojname = request.POST.getlist('txtprojname')
		arrnojob = request.POST.getlist('txtnojob')
		arrstdt = request.POST.getlist('txtstdt')
		arrrepstdt = request.POST.getlist('txtrepstdt')
		arrlatrundt = request.POST.getlist('txtlatrundt')
		arrlatrundur = request.POST.getlist('txtlatrundur')
		arravgrundur = request.POST.getlist('txtavgrundur')
		arrpo2s3 = request.POST.getlist('txtpo2s3')
#		arrvalsumtime = request.POST.getlist('hidvalsumtime')
		
		frmsysdt = datetime.datetime.now()
		frmsysdt = str(frmsysdt)[:19]
		p = 0
		while p < len(arrprojid):
			frmprojid = arrprojid[p]
			frmprojname = arrprojname[p]
			frmnojob = arrnojob[p]
			frmstdt = arrstdt[p]
			frmrepstdt = arrrepstdt[p]
			frmlatrundt = str(arrlatrundt[p])[:19]
			frmlatrundur = arrlatrundur[p]
			frmavgrundur = arravgrundur[p]
			frmpo2s3 = arrpo2s3[p]
#			frmvalsumtime = arrvalsumtime[p]
			cursor = connection.cursor()
			connection.commit()
			cursor.execute("update wisdom_meta_data.wisdom_jobproject set project_name = %s, number_of_jobs = %s, scheduled_start_time = %s, report_timezone_scheduled_time = %s, latest_run_date = %s, latest_run_duration_minutes = %s, validation_wrapper_summary_time = %s, postgres_to_redshift_process = %s, modified_at = %s, modified_by = %s, pk_client = 1, pk_venue = 1 where project_id = %s" ,(frmprojname, frmnojob, frmstdt, frmrepstdt, frmlatrundt, frmlatrundur, frmavgrundur, frmpo2s3, frmsysdt, usid, frmprojid))
       			cursor.close()
			p = p + 1
			
		return HttpResponseRedirect('/wai_mngprojob/')

#Function to insert the records to table "wisdom_meta_data.wisdom_jobproject"
def wai_insprojdet(request):
	if request.method == 'POST':
		usid = request.session.get("userid")
		usem = request.session.get("username")
		ustyp = request.session.get("usertype")

		frmprojid = request.POST.get('txtcrtprojid')
		frmprojname = request.POST.get('txtcrtprojname')
		frmnojob = request.POST.get('txtcrtprojjobs')
		frmstdt = request.POST.get('txtcrtprojst')
		frmrepstdt = request.POST.get('txtcrtprojstrep')
		frmpo2s3 = request.POST.get('ddlcrtpg2s3')
		#frmvalsumtime = request.POST.get('txtcrtprojvaltm')
		
		frmsysdt = datetime.datetime.now()
		frmsysdt = str(frmsysdt)[:19]
		
		cursor = connection.cursor()
		connection.commit()
		#cursor.execute("insert into wisdom_meta_data.wisdom_jobproject (project_id, project_name, number_of_jobs, scheduled_start_time, report_timezone_scheduled_time, postgres_to_redshift_process, validation_wrapper_summary_time, created_at, created_by,  pk_client, pk_venue, latest_run_date, latest_run_duration_minutes, average_run_duration_minutes, modified_at, modified_by) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 1, %s, 0, 0, %s, %s)", (frmprojid, frmprojname, frmnojob, frmstdt, frmrepstdt, frmpo2s3, frmvalsumtime, frmsysdt, usid, frmsysdt, frmsysdt, usid))
		cursor.execute("insert into wisdom_meta_data.wisdom_jobproject (project_id, project_name, number_of_jobs, scheduled_start_time, report_timezone_scheduled_time, postgres_to_redshift_process, created_at, created_by, pk_client, pk_venue, latest_run_date, latest_run_duration_minutes, average_run_duration_minutes, modified_at, modified_by) values (%s, %s, %s, %s, %s, %s, %s, %s, 1, 1, %s, 0, 0, %s, %s)", (frmprojid, frmprojname, frmnojob, frmstdt, frmrepstdt, frmpo2s3, frmsysdt, usid, frmsysdt, frmsysdt, usid))
       		cursor.close()
			
		return HttpResponseRedirect('/wai_mngprojob/')

#Function to check Project ID/Project Name already exist or not "wisdom_meta_data.wisdom_jobproject"
def wai_ext_projid_name(request):
	masid = 0
	if request.method == 'POST':
		if 'projid' in request.POST:
			projid = request.POST.get('projid')
			prodetcur = connection.cursor()
			prodetcur.execute("select project_id, project_name from wisdom_meta_data.wisdom_jobproject where project_id = %s", [projid])
			masrow = prodetcur.fetchall()
			prodetcur.close()
			
			for massing in masrow:
				masid = massing[0]
		
			if masid is None:
				masid = 0
		
		elif 'projname' in request.POST:
			projname = request.POST.get('projname')
			prodetcur= connection.cursor()
			prodetcur.execute("select project_id, project_name from wisdom_meta_data.wisdom_jobproject where project_name like %s", [projname])
			masrow = prodetcur.fetchall()
			prodetcur.close()
			
			for massing in masrow:
				masid = massing[0]
		
			if masid is None:
				masid = 0
		else:
			masid = 0
		
	return HttpResponse(masid)

#Function to check Project ID/Project Name already exist or not "wisdom_meta_data.wisdom_jobproject" while updating the project name	
def wai_updprojidnaext(request):
	extprojid = 0
	if request.method == 'POST':
		if 'projid' in request.POST:
			projid = request.POST.get('projid')
			projname = request.POST.get('projname')
			prodetcur= connection.cursor()
			prodetcur.execute("select project_id, project_name from wisdom_meta_data.wisdom_jobproject where project_name like %s and project_id <> %s", (projname, projid))
			dsprojdet = prodetcur.fetchall()
			prodetcur.close()
			
			for pidnasing in dsprojdet:
				extprojid = pidnasing[0]
		
			if extprojid is None:
				extprojid = 0				
		else:
			extprojid = 0
		
	return HttpResponse(extprojid)
		
#Function to update the records to table "wisdom_meta_data.wisdom_jobmaster"
def upprojobs(request):
	if request.method == 'POST':
		arrjobid = request.POST.getlist('hidjobid')
		arrjobname = request.POST.getlist('txtjobname')
		arrjobdesc =  request.POST.getlist('txtjobdesc')
		arrfrequ =  request.POST.getlist('txtfrequ')
		arrcate =  request.POST.getlist('txtcate')
		arractive =  request.POST.getlist('txtactive')
		arrhighfreq =  request.POST.getlist('txthighfreq')
		arrjobemthre =  request.POST.getlist('txtjobemthre')
		arremacount =  request.POST.getlist('txtemacount')
		arrincstdt =  request.POST.getlist('txtincstdt')
		arrinceddt =  request.POST.getlist('txtinceddt')

		frmprojid = request.GET.get('pid')
		i = 0
		while i < len(arrjobid):
			frmprojobid = arrjobid[i]
			frmjobname = arrjobname[i]
			frmjobdesc = arrjobdesc[i]
			frmfrequ = arrfrequ[i]
			frmcate = arrcate[i]
			frmactive = arractive[i]
			frmhighfreq = arrhighfreq[i]
			frmjobemthre = arrjobemthre[i]
			frmemacount = arremacount[i]
			frmincstdt = str(arrincstdt[i])[:19]
			frminceddt = str(arrinceddt[i])[:19]
			cursor = connection.cursor()
			if frminceddt != "" :
				cursor.execute("update wisdom_meta_data.wisdom_jobmaster set job_name = %s, job_description = %s, frequency = %s, category = %s, active = %s, is_high_frequency_job = %s, success_email_threshold = %s, success_email_counter = %s, incremental_baseline_date_start = %s, incremental_baseline_date_end = %s, pk_client = 1, pk_venue = 1 where job_id = %s", (frmjobname, frmjobdesc, frmfrequ, frmcate, frmactive, frmhighfreq, frmjobemthre, frmemacount, frmincstdt, frminceddt, frmprojobid))
			else:
				cursor.execute("update wisdom_meta_data.wisdom_jobmaster set job_name = %s, job_description = %s, frequency = %s, category = %s, active = %s, is_high_frequency_job = %s, success_email_threshold = %s, success_email_counter = %s, incremental_baseline_date_start = %s, pk_client = 1, pk_venue = 1 where job_id = %s", (frmjobname, frmjobdesc, frmfrequ, frmcate, frmactive, frmhighfreq, frmjobemthre, frmemacount, frmincstdt, frmprojobid))

			#cursor.execute("update wisdom_meta_data.wisdom_jobmaster set job_name = %s, job_description = %s, frequency = %s, category = %s, active = %s, is_high_frequency_job = %s, success_email_threshold = %s, success_email_counter = %s, incremental_baseline_date_start = %s, incremental_baseline_date_end = %s, pk_client = 1, pk_venue = 1 where job_id = %s", (frmjobname, frmjobdesc, frmfrequ, frmcate, frmactive, frmhighfreq, frmjobemthre, frmemacount, frmincstdt, frminceddt, frmprojobid))
			connection.commit()
       			cursor.close()
			i = i + 1

		strRedirect = '/wai_mngprojob/?pid=' + frmprojid

		return HttpResponseRedirect(strRedirect)

#Function to insert the records to table "wisdom_meta_data.wisdom_jobmaster"
def wai_insjobdet(request):
	if request.method == 'POST':
		usid = request.session.get("userid")
		usem = request.session.get("username")
		ustyp = request.session.get("usertype")
		
		frmprojid = request.GET.get('pid')
		frmjobid = request.POST.get('txtcrtjobid')
		frmjobname = request.POST.get('txtcrtjobname')
		frmjobdesc = request.POST.get('txtcrtjobdesc')
		frmjobfreq = request.POST.get('txtcrtjobfreq')
		frmjobcat = request.POST.get('txtcrtjobcat')
		frmjobstatus = request.POST.get('ddlcrtjobact')
		frmjobhifreq = request.POST.get('dllcrtjobhifreq')
		frmjobinstdate = request.POST.get('txtcrtjobinstdate')
		frmjobineddate = request.POST.get('txtcrtjobineddate')
		
		frmsysdt = datetime.datetime.now()
		frmsysdt = str(frmsysdt)[:19]

		#getjidcur = connection.cursor()
		#getjidcur.execute("SELECT (max(job_id)+1) as job_id from wisdom_meta_data.wisdom_jobmaster where project_id = %s", [frmprojid])
		#jidrow = getjidcur.fetchall()
		
		#frmjobid = ""
		#for jidsing in jidrow:
		#	frmjobid = jidsing[0]
		
		#if frmjobid is None:
		#	frmjobid = int(frmprojid) + 1
		#getjidcur.close()
		
		cursor = connection.cursor()
		connection.commit()
		cursor.execute("insert into wisdom_meta_data.wisdom_jobmaster (job_id, project_id, job_name, job_description, frequency, category, active, is_high_frequency_job, incremental_baseline_date_start, incremental_baseline_date_end, pk_client, pk_venue, createddate, createdby) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 1, %s, %s)",(frmjobid, frmprojid, frmjobname, frmjobdesc, frmjobfreq, frmjobcat, frmjobstatus, frmjobhifreq, frmjobinstdate, frmjobineddate, frmsysdt, usid))
		cursor.close()
			
		strRedirect = '/wai_mngprojob/?pid=' + frmprojid
		return HttpResponseRedirect(strRedirect)
	else:
		return HttpResponseRedirect('/wai_mngprojob/')

#Function to check Job ID/Job Name already exist or not "wisdom_meta_data.wisdom_jobmaster" while inserting the job details
def wai_extjobidna(request):
	extjobid = 0
	if request.method == 'POST':
		if 'jobid' in request.POST:
			jobid = request.POST.get('jobid')
			jobdetcur = connection.cursor()
			jobdetcur.execute("select job_id, project_id, job_name from wisdom_meta_data.wisdom_jobmaster where job_id = %s", [jobid])
			dsjobdet = jobdetcur.fetchall()
			jobdetcur.close()
			
			for jodesing in dsjobdet:
				extjobid = jodesing[0]
		
			if extjobid is None:
				extjobid = 0
		
		elif 'jobname' in request.POST:
			jobname = request.POST.get('jobname')
			jobdetcur= connection.cursor()
			jobdetcur.execute("select job_id, project_id, job_name from wisdom_meta_data.wisdom_jobmaster where job_name like %s", [jobname])
			dsjobdet = jobdetcur.fetchall()
			jobdetcur.close()
			
			for jodesing in dsjobdet:
				extjobid = jodesing[0]
		
			if extjobid is None:
				extjobid = 0				
		else:
			extjobid = 0
		
	return HttpResponse(extjobid)

#Function to check Job Name already exist or not "wisdom_meta_data.wisdom_jobmaster" while updating the job name
def wai_updextjobidna(request):
	extjobid = 0
	if request.method == 'POST':
		if 'jobid' in request.POST:
			jobid = request.POST.get('jobid')
			jobname = request.POST.get('jobname')
			jobdetcur = connection.cursor()
			jobdetcur.execute("select job_id, project_id, job_name from wisdom_meta_data.wisdom_jobmaster where job_name like %s and job_id <> %s", (jobname, jobid))
			dsjobdet = jobdetcur.fetchall()
			jobdetcur.close()
			
			for jodesing in dsjobdet:
				extjobid = jodesing[0]
		
			if extjobid is None:
				extjobid = 0				
		else:
			extjobid = 0
		
	return HttpResponse(extjobid)

#Manage project/Job Ends

#Manage Process Monitoring Starts
#This function will show the all the job run details with filter option (Filter like based on the project, status and active)
def wai_mngprocmoni(request):
	if 'userid' not in request.session:
		return HttpResponseRedirect('/wai_login/')
	else:
		projdet = actsta = projid = projsta = procdet = "";
		usid = request.session.get("userid")
		usem = request.session.get("username")
		ustyp = request.session.get("usertype")

		ddlcursor = connection.cursor()
       		ddlcursor.execute("SELECT project_id, project_name, scheduled_start_time, number_of_jobs, latest_run_date, latest_run_duration_minutes, average_run_duration_minutes, created_at, modified_at, created_by, modified_by, report_timezone_scheduled_time, validation_wrapper_summary_time, pk_client, pk_venue, postgres_to_redshift_process FROM wisdom_meta_data.wisdom_jobproject order by project_id asc")

	        desc = ddlcursor.description
       		projdet = [
               		dict(zip([col[0] for col in desc], row))
                	for row in ddlcursor.fetchall()
       	        	]
	        ddlcursor.close()

#		Here we are checking the any filter is available, if there is a filter available it will execute the following code
		if request.method == 'POST':
			projid = request.POST.get("ddlproject")
			actsta = request.POST.get("ddlactive")
			projsta = request.POST.get("ddlstatus")

			jobrundt = str(request.POST.get("txtjobdate"))[:10]
			jobrundt = datetime.datetime.strptime(jobrundt, '%m/%d/%Y').strftime('%Y-%m-%d')

			strsysdt = request.POST.get("txtjobdate")

			strstdt = jobrundt + " 00:00:00.000"
			streddt = jobrundt + " 23:59:59.000"
			
			strsysdt = request.POST.get("txtjobdate")

			projstatus = ""
			if projsta == "S":
				projstatus = "SUCCEEDED"
			elif projsta == "F":
				projstatus = "FAILED"
			elif projsta == "P":
				projstatus = "STARTED"

			cursor = connection.cursor()			
			if projid != "":
        			cursor.execute("select jp.project_id, jp.project_name, jp.number_of_jobs, jp.scheduled_start_time, (select count(jobrun_id) from wisdom_meta_data.wisdom_jobrun jr, wisdom_meta_data.wisdom_jobmaster jm where jr.job_id = jm.job_id and jm.project_id = jp.project_id and jr.startdatetime between %s and %s) as total_job_run, (select count(jobrun_id) from wisdom_meta_data.wisdom_jobrun jr, wisdom_meta_data.wisdom_jobmaster jm where jr.job_id = jm.job_id and jm.project_id = jp.project_id and jr.startdatetime between %s and %s and jr.status = 'SUCCEEDED') as total_succ_job, (select count(jobrun_id) from wisdom_meta_data.wisdom_jobrun jr, wisdom_meta_data.wisdom_jobmaster jm where jr.job_id = jm.job_id and jm.project_id = jp.project_id and jr.startdatetime between %s and %s and jr.status = 'FAILED') as total_fail_job, (SELECT count(*) FROM validation.wisdom_data_validation_details vd, validation.wisdom_data_validation_master vm WHERE vd.validation_id = vm.id and vd.project_id = jp.project_id and vd.validation_success = 'N' and vm.priority = 1 and run_date_time between %s and %s) as val_fail_job, (SELECT count(*) FROM validation.wisdom_data_validation_details vd, validation.wisdom_data_validation_master vm WHERE vd.validation_id = vm.id and vd.project_id = jp.project_id and vd.validation_success = 'Y' and run_date_time between %s and %s) as val_succ_job from wisdom_meta_data.wisdom_jobproject jp where jp.project_id = %s order by project_id asc;", (strstdt, streddt, strstdt, streddt, strstdt, streddt, strstdt, streddt, strstdt, streddt, projid))
			else:
				cursor.execute("select jp.project_id, jp.project_name, jp.number_of_jobs, jp.scheduled_start_time, (select count(jobrun_id) from wisdom_meta_data.wisdom_jobrun jr, wisdom_meta_data.wisdom_jobmaster jm where jr.job_id = jm.job_id and jm.project_id = jp.project_id and jr.startdatetime between %s and %s) as total_job_run, (select count(jobrun_id) from wisdom_meta_data.wisdom_jobrun jr, wisdom_meta_data.wisdom_jobmaster jm where jr.job_id = jm.job_id and jm.project_id = jp.project_id and jr.startdatetime between %s and %s and jr.status = 'SUCCEEDED') as total_succ_job, (select count(jobrun_id) from wisdom_meta_data.wisdom_jobrun jr, wisdom_meta_data.wisdom_jobmaster jm where jr.job_id = jm.job_id and jm.project_id = jp.project_id and jr.startdatetime between %s and %s and jr.status = 'FAILED') as total_fail_job, (SELECT count(*) FROM validation.wisdom_data_validation_details vd, validation.wisdom_data_validation_master vm WHERE vd.validation_id = vm.id and vd.project_id = jp.project_id and vd.validation_success = 'N' and vm.priority = 1 and run_date_time between %s and %s) as val_fail_job, (SELECT count(*) FROM validation.wisdom_data_validation_details vd, validation.wisdom_data_validation_master vm WHERE vd.validation_id = vm.id and vd.project_id = jp.project_id and vd.validation_success = 'Y' and run_date_time between %s and %s) as val_succ_job from wisdom_meta_data.wisdom_jobproject jp order by project_id asc;", (strstdt, streddt, strstdt, streddt, strstdt, streddt, strstdt, streddt, strstdt, streddt))

			desc = cursor.description
       			procdet = [
				dict(zip([col[0] for col in desc], row))
		        	for row in cursor.fetchall()
				]
			cursor.close()

#		if there is no filter it will execute the following code
		else:		
			strsysdt = datetime.datetime.now()
			strsysdt = str(strsysdt)[:10]

			strstdt = strsysdt + " 00:00:00.000"
			streddt = strsysdt + " 23:59:59.000"

			strsysdt = datetime.datetime.strptime(strsysdt, '%Y-%m-%d').strftime('%m/%d/%Y')

			cursor = connection.cursor()			
			cursor.execute("select jp.project_id, jp.project_name, jp.number_of_jobs, jp.scheduled_start_time, (select count(jobrun_id) from wisdom_meta_data.wisdom_jobrun jr, wisdom_meta_data.wisdom_jobmaster jm where jr.job_id = jm.job_id and jm.project_id = jp.project_id and jr.startdatetime between %s and %s) as total_job_run, (select count(jobrun_id) from wisdom_meta_data.wisdom_jobrun jr, wisdom_meta_data.wisdom_jobmaster jm where jr.job_id = jm.job_id and jm.project_id = jp.project_id and jr.startdatetime between %s and %s and jr.status = 'SUCCEEDED') as total_succ_job, (select count(jobrun_id) from wisdom_meta_data.wisdom_jobrun jr, wisdom_meta_data.wisdom_jobmaster jm where jr.job_id = jm.job_id and jm.project_id = jp.project_id and jr.startdatetime between %s and %s and jr.status = 'FAILED') as total_fail_job, (SELECT count(*) FROM validation.wisdom_data_validation_details vd, validation.wisdom_data_validation_master vm WHERE vd.validation_id = vm.id and vd.project_id = jp.project_id and vd.validation_success = 'N' and vm.priority = 1 and run_date_time between %s and %s) as val_fail_job, (SELECT count(*) FROM validation.wisdom_data_validation_details vd, validation.wisdom_data_validation_master vm WHERE vd.validation_id = vm.id and vd.project_id = jp.project_id and vd.validation_success = 'Y' and run_date_time between %s and %s) as val_succ_job from wisdom_meta_data.wisdom_jobproject jp order by project_id asc;", (strstdt, streddt, strstdt, streddt, strstdt, streddt, strstdt, streddt, strstdt, streddt))
			desc = cursor.description
       			procdet = [
				dict(zip([col[0] for col in desc], row))
		        	for row in cursor.fetchall()
				]
			cursor.close()

		pgcur = connection.cursor()
		pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
		desc = pgcur.description
       		pgdet = [
			dict(zip([col[0] for col in desc], row))
	       		for row in pgcur.fetchall()
			]
		pgcur.close()

		cursysdt = datetime.datetime.now()
		cursysdt = str(cursysdt)[:10]
		cursysdt = datetime.datetime.strptime(cursysdt, '%Y-%m-%d').strftime('%m/%d/%Y')

		clientid = ""
		if 'clientid' in request.session:
			clientid = request.session["clientid"]

		clidetcur = connection.cursor()
		clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
		desc = clidetcur.description
		clidet = [
			dict(zip([col[0] for col in desc], row))
			for row in clidetcur.fetchall()
		]
		for row in clidet:
			if clientid == "":
				clientid = row["pk_client"]
		clidetcur.close()
			
		vendetcur = connection.cursor()
		vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
		desc = vendetcur.description
		vendet = [
			dict(zip([col[0] for col in desc], row))
			for row in vendetcur.fetchall()
		]
		vendetcur.close()
		
		return render(request, 'wai_mngprocmoni.html', {'projdet': projdet , 'actsta': actsta , 'projid': projid , 'status': projsta, 'procdet': procdet, 'hid': "3", 'usna': usem, 'seldt': strsysdt, 'ustyp': ustyp, 'pgdet': pgdet, 'cursysdt': cursysdt, 'clidet': clidet, 'vendet': vendet })

def wai_procsjobs(request):
	if 'userid' not in request.session:
		return HttpResponseRedirect('/wai_login/')
	else:
		projdet = actsta = projid = projsta = procdet = "";
		usid = request.session.get("userid")
		usem = request.session.get("username")
		ustyp = request.session.get("usertype")

		pgcur = connection.cursor()
		pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
		desc = pgcur.description
       		pgdet = [
			dict(zip([col[0] for col in desc], row))
	       		for row in pgcur.fetchall()
			]
		pgcur.close()

		if request.method == 'POST':
			projid = request.POST.get("hidselpid")
			jobrundt = request.POST.get("hidseldt")
			jobrundt = datetime.datetime.strptime(jobrundt, '%m/%d/%Y').strftime('%Y-%m-%d')

			strsysdt = request.POST.get("txtjobdate")
			strstdt = jobrundt + " 00:00:00.000"
			streddt = jobrundt + " 23:59:59.000"
			
			strsysdt = request.POST.get("hidseldt")
	
			cursor = connection.cursor()			
			if projid != "":
	       			cursor.execute("select jp.project_id, jp.project_name, jp.number_of_jobs, jp.scheduled_start_time, (select count(jobrun_id) from wisdom_meta_data.wisdom_jobrun jr, wisdom_meta_data.wisdom_jobmaster jm where jr.job_id = jm.job_id and jm.project_id = jp.project_id and jr.startdatetime between %s and %s) as total_job_run, (select count(jobrun_id) from wisdom_meta_data.wisdom_jobrun jr, wisdom_meta_data.wisdom_jobmaster jm where jr.job_id = jm.job_id and jm.project_id = jp.project_id and jr.startdatetime between %s and %s and jr.status = 'SUCCEEDED') as total_succ_job, (select count(jobrun_id) from wisdom_meta_data.wisdom_jobrun jr, wisdom_meta_data.wisdom_jobmaster jm where jr.job_id = jm.job_id and jm.project_id = jp.project_id and jr.startdatetime between %s and %s and jr.status = 'FAILED') as total_fail_job, (SELECT count(*) FROM validation.wisdom_data_validation_details vd, validation.wisdom_data_validation_master vm WHERE vd.validation_id = vm.id and vd.project_id = jp.project_id and vd.validation_success = 'N' and vm.priority = 1 and run_date_time between %s and %s) as val_fail_job, (SELECT count(*) FROM validation.wisdom_data_validation_details vd, validation.wisdom_data_validation_master vm WHERE vd.validation_id = vm.id and vd.project_id = jp.project_id and vd.validation_success = 'Y' and run_date_time between %s and %s) as val_succ_job from wisdom_meta_data.wisdom_jobproject jp where jp.project_id = %s order by project_id asc;", (strstdt, streddt, strstdt, streddt, strstdt, streddt, strstdt, streddt, strstdt, streddt, projid))
				
			procdet = cursor.fetchall()
			projname = projid = numofjob = totrunjobs = schestdt = totsuccjobs = totfailjobs = totvalsuccjobs = totvalfailjobs = ""
			
			for procsing in procdet:
				projid = procsing[0]
				projname = procsing[1]
				numofjob = procsing[2]
				schestdt = procsing[3]
				totrunjobs = procsing[4]
				totsuccjobs = procsing[5]
				totfailjobs = procsing[6]
				totvalsuccjobs = procsing[8]
				totvalfailjobs = procsing[7]

			cursor.close()
		
			jobcur = connection.cursor()
			jobcur.execute("select jm.job_id, jm.job_name, jm.job_description, jm.project_id, jm.frequency, jm.active, jm.is_high_frequency_job, jm.success_email_threshold, jm.success_email_counter, jr.jobrun_id, jr.jobparameter, jr.recordsread, jr.recordsinserted, jr.recordsupdated, jr.recordsdeleted, jr.startdatetime, jr.enddatetime, jr.status, jr.comments, jr.executiontimeminute from wisdom_meta_data.wisdom_jobmaster jm, wisdom_meta_data.wisdom_jobrun jr where jm.job_id = jr.job_id and jm.project_id = %s and jr.startdatetime between %s and %s order by jr.jobrun_id desc", (projid, strstdt, streddt))
			desc = jobcur.description
	       		procjobdet = [
				dict(zip([col[0] for col in desc], row))
				for row in jobcur.fetchall()
				]
			jobcur.close()

			jobrundt = request.POST.get("hidseldt")
			jobrunddlsta = request.POST.get("hidselstatus")
		
			cursysdt = datetime.datetime.now()
			cursysdt = str(cursysdt)[:10]
			cursysdt = datetime.datetime.strptime(cursysdt, '%Y-%m-%d').strftime('%m/%d/%Y')

			clientid = ""
			if 'clientid' in request.session:
				clientid = request.session["clientid"]

			clidetcur = connection.cursor()
			clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
			desc = clidetcur.description
			clidet = [
				dict(zip([col[0] for col in desc], row))
				for row in clidetcur.fetchall()
				]
			for row in clidet:
				if clientid == "":
					clientid = row["pk_client"]
			clidetcur.close()
			
			vendetcur = connection.cursor()
			vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
			desc = vendetcur.description
			vendet = [
				dict(zip([col[0] for col in desc], row))
				for row in vendetcur.fetchall()
			]
			vendetcur.close()
		
			return render(request, 'wai_mngprocjob.html', {'projid': projid , 'projname': projname, 'numofjob': numofjob, 'totrunjobs': totrunjobs, 'procjobdet': procjobdet, 'hid': "3", 'usna': usem, 'curdt': strsysdt, 'ustyp': ustyp, 'pgdet': pgdet, 'schestdt': schestdt, 'jobrundt': jobrundt, 'jobrunddlsta': jobrunddlsta, 'totsuccjobs': totsuccjobs, 'totfailjobs': totfailjobs, 'totvalsuccjobs': totvalsuccjobs, 'totvalfailjobs': totvalfailjobs, 'cursysdt': cursysdt, 'clidet': clidet, 'vendet': vendet })
		else:
			return HttpResponseRedirect('/wai_mngprocmoni/')
#Manage Process Monitoring Ends


#Manage Client/Venue Starts
def wai_mngcliven(request):
	if 'userid' not in request.session:
		return HttpResponseRedirect('/wai_login/')
	else:
		usid = request.session.get("userid")
		usem = request.session.get("username")
		ustyp = request.session.get("usertype")
		
		strsysdt = datetime.datetime.now()
		strsysdt = str(strsysdt)[:19]
		
		intcount = 4
		if request.method == 'POST':
			arrcliid = request.POST.getlist('hidedclieid')
			arrcliname = request.POST.getlist('txtcliname')
			arrcliaddr =  request.POST.getlist('txtcliaddr')
			arrclicity =  request.POST.getlist('txtclicity')
			arrclista =  request.POST.getlist('txtclista')
			arrclicount =  request.POST.getlist('txtclicountry')
			arrclicur =  request.POST.getlist('txtclicurr')
			arrclisotz =  request.POST.getlist('txtclisourtz')
			arrcliretz =  request.POST.getlist('txtclireptz')

			i = 0
			while i < len(arrcliname):
				strCliId = arrcliid[i]
				strCliNa = arrcliname[i]
				strCliAdr = arrcliaddr[i]
				strCliCit = arrclicity[i]
				strCliSta = arrclista[i]
				strCliCout = arrclicount[i]
				strCliCur = arrclicur[i]
				strCliSoTz = arrclisotz[i]
				strCliReTz = arrcliretz[i]
				
				updclicur = connection.cursor()
				updclicur.execute("update mart.dim_client set client_name = %s, address = %s, city = %s, state = %s, country = %s, client_currency = %s, source_timezone = %s, report_timezone = %s, dw_updated_by = %s, dw_update_date = %s where pk_client = %s", (strCliNa, strCliAdr, strCliCit, strCliSta, strCliCout, strCliCur, strCliSoTz, strCliReTz, usid, strsysdt, strCliId))
				connection.commit()
       				i = i + 1
				
			return HttpResponseRedirect('/wai_mngcliven/')
		else:
			pgcur = connection.cursor()
			pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
			desc = pgcur.description
	       		pgdet = [
				dict(zip([col[0] for col in desc], row))
	    	   		for row in pgcur.fetchall()
				]
			pgcur.close()

			clicur = connection.cursor()
			clicur.execute("select pk_client, client_name, address, city, state, country, createdate, dw_created_by, dw_create_date, dw_updated_by, dw_update_date, jobrun_id, source_timezone, report_timezone, client_currency from mart.dim_client order by pk_client asc")
	        	desc = clicur.description
	       		clidet = [
    	           		dict(zip([col[0] for col in desc], row))
        	        	for row in clicur.fetchall()
        		        ]
		        clicur.close()
			
			clientid = ""
			if 'clientid' in request.session:
				clientid = request.session["clientid"]

			clidetcur = connection.cursor()
			clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
			desc = clidetcur.description
			ddlclidet = [
				dict(zip([col[0] for col in desc], row))
				for row in clidetcur.fetchall()
			]
			for row in ddlclidet:
				if clientid == "":
					clientid = row["pk_client"]
			clidetcur.close()
			
			vendetcur = connection.cursor()
			vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
			desc = vendetcur.description
			vendet = [
				dict(zip([col[0] for col in desc], row))
				for row in vendetcur.fetchall()
			]
			vendetcur.close()

			return render(request, 'wai_mngcliven.html', {'clidet': clidet, 'hid': 4, 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'ddlclidet': ddlclidet, 'vendet': vendet })

#Function to check Client ID/Client Name already exist or not "mart.dim_client"
def wai_ext_clientid_name(request):
	clieid = 0
	if request.method == 'POST':
		if 'clientid' in request.POST:
			clientid = request.POST.get('clientid')
			clidetcur = connection.cursor()
			clidetcur.execute("select pk_client, client_name from mart.dim_client where pk_client = %s", [clientid])
			masrow = clidetcur.fetchall()
			clidetcur.close()
			
			for massing in masrow:
				clieid = massing[0]
		
			if clieid is None:
				clieid = 0
		
		elif 'clientname' in request.POST:
			cliename = request.POST.get('clientname')
			clidetcur= connection.cursor()
			clidetcur.execute("select pk_client, client_name from mart.dim_client where client_name like %s", [cliename])
			masrow = clidetcur.fetchall()
			clidetcur.close()
			
			for massing in masrow:
				clieid = massing[0]
		
			if clieid is None:
				clieid = 0
		else:
			clieid = 0
		
	return HttpResponse(clieid)

#Function to check Client ID/Client Name already exist or not "mart.dim_client" while updating the client name
def wai_extupdcliidna(request):
	clieid = 0
	if request.method == 'POST':
		if 'clientID' in request.POST:
			clientID = request.POST.get('clientID')
			clientname = request.POST.get('clientname')
			clidetcur = connection.cursor()
			clidetcur.execute("select pk_client, client_name from mart.dim_client where client_name like %s and pk_client <> %s", (clientname, clientID))
			clidetrow = clidetcur.fetchall()
			clidetcur.close()
			
			for clidetsing in clidetrow:
				clieid = clidetsing[0]
		
			if clieid is None:
				clieid = 0
		else:
			clieid = 0
		
	return HttpResponse(clieid)
	

def wai_insclidet(request):
	usid = request.session.get("userid")
	usem = request.session.get("username")
	ustyp = request.session.get("usertype")
		
	strsysdt = datetime.datetime.now()
	strsysdt = str(strsysdt)[:10]
		
	if request.method == 'POST':
		strCliId = request.POST.get('txtcrtcliid')
		strCliNa = request.POST.get('txtcrtcliename')
		strCliAdr =  request.POST.get('txtcrtcliaddr')
		strCliCit =  request.POST.get('txtcrtclicity')
		strCliSta =  request.POST.get('txtcrtclistate')
		strCliCout =  request.POST.get('txtcrtclicount')
		strCliCur =  request.POST.get('txtcrtclicur')
		strCliSoTz =  request.POST.get('txtcrtsourtz')
		strCliReTz =  request.POST.get('txtcrtreptz')

		insclicur = connection.cursor()
		insclicur.execute("insert into mart.dim_client (pk_client, client_name, address, city, state, country, client_currency, source_timezone, report_timezone, dw_created_by, createdate) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (strCliId, strCliNa, strCliAdr, strCliCit, strCliSta, strCliCout, strCliCur, strCliSoTz, strCliReTz, usid, strsysdt))
		connection.commit()
       		insclicur.close()		
	
	return HttpResponseRedirect('/wai_mngcliven/')

def wai_clivendet(request):
	if 'userid' not in request.session:
		return HttpResponseRedirect('/wai_login/')
	else:
		usid = request.session.get("userid")
		usem = request.session.get("username")
		ustyp = request.session.get("usertype")
		
		strsysdt = datetime.datetime.now()
		strsysdt = str(strsysdt)[:19]
		
		cliid = request.GET.get("cid")
		
		if request.method == 'POST':
			arrvenid = request.POST.getlist('hidvenuid')
			arrvenname = request.POST.getlist('txtvenuname')
			arrvendesc = request.POST.getlist('txtvenudesc')
			arrvenaddr =  request.POST.getlist('txtvenuaddr')
			arrvencity =  request.POST.getlist('txtvenucity')			
			arrvencount =  request.POST.getlist('txtvenucount')
			arrvencur =  request.POST.getlist('txtvenucur')
			arrvenretz =  request.POST.getlist('txtvenureptz')
			arrvenorg =  request.POST.getlist('txtvenuorgna')
			arrvenuid =  request.POST.getlist('txtvenuuuid')	

			i = 0
			while i < len(arrvenid):
				strVenId = arrvenid[i]
				strVenNa = arrvenname[i]
				strVenDesc = arrvendesc[i]
				strVenAdr = arrvenaddr[i]
				strVenCit = arrvencity[i]
				strVenCout = arrvencount[i]
				strVenCur = arrvencur[i]
				strVenReTz = arrvenretz[i]
				strVenOrg = arrvenorg[i]
				strVenUID = arrvenuid[i]
				
				updvencur = connection.cursor()
				updvencur.execute("update mart.dim_venue set venue_name = %s, description = %s, address = %s, city = %s, country = %s, venue_currency = %s, report_timezone = %s, organization_name = %s, venue_uuid = %s, dw_updated_by = %s, dw_update_date = %s where pk_venue = %s", (strVenNa, strVenDesc, strVenAdr, strVenCit, strVenCout, strVenCur, strVenReTz, strVenOrg, strVenUID, usid, strsysdt, strVenId))
				connection.commit()
       				i = i + 1
			
			strRedirect = "/wai_clivendet/?cid=" + cliid
			return HttpResponseRedirect(strRedirect)
		else:
			pgcur = connection.cursor()
			pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
			desc = pgcur.description
	       		pgdet = [
				dict(zip([col[0] for col in desc], row))
	    	   		for row in pgcur.fetchall()
				]
			pgcur.close()

			clicur = connection.cursor()
			clicur.execute("select pk_client, client_name, address, city, state, country, client_currency, source_timezone, report_timezone, createdate, dw_created_by, dw_create_date, dw_updated_by, dw_update_date, jobrun_id from mart.dim_client where pk_client = %s", [cliid])
	        	dsclidet = clicur.fetchall()

			clientid = cliname = cliaddress = clicity = clistate = clicountry = clicurrency = clireptz = clisotz = ""
			for sinclidet in dsclidet:
				clientid = sinclidet[0]
				cliname = sinclidet[1]
				cliaddress = sinclidet[2]
				clicity = sinclidet[3]
				clistate = sinclidet[4]
				clicountry = sinclidet[5]
				clicurrency = sinclidet[6]
				clireptz = sinclidet[7]
				clisotz = sinclidet[8]
	       		clicur.close()
			
			vencur = connection.cursor()
			vencur.execute("select pk_venue, venue_name, description, address, city, country, createdate, dw_created_by, dw_create_date, dw_updated_by, dw_update_date, jobrun_id, report_timezone, pk_client, venue_currency, organization_name, venue_uuid from mart.dim_venue where pk_client = %s", [cliid])
	        	desc = vencur.description
	       		venuedet = [
    	           		dict(zip([col[0] for col in desc], row))
        	        	for row in vencur.fetchall()
        		        ]
		        clicur.close()

			ddlcliid = ""
			clidetcur = connection.cursor()
			clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
			desc = clidetcur.description
			clidet = [
				dict(zip([col[0] for col in desc], row))
				for row in clidetcur.fetchall()
				]
			for row in clidet:
				if ddlcliid == "":
					ddlcliid = row["pk_client"]
			clidetcur.close()
			
			vendetcur = connection.cursor()
			vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[ddlcliid])
			desc = vendetcur.description
			vendet = [
				dict(zip([col[0] for col in desc], row))
				for row in vendetcur.fetchall()
			]
			vendetcur.close()
				
			return render(request, 'wai_clivendet.html', {'clientid': clientid, 'cliname': cliname, 'cliaddress': cliaddress, 'clicity': clicity, 'clistate': clistate, 'clicountry': clicountry, 'clicurrency': clicurrency, 'clireptz': clireptz, 'clisotz': clisotz, 'hid': 4, 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'venuedet': venuedet, 'clidet': clidet, 'vendet': vendet })

#Function to check Venue ID/Venue Name already exist or not "mart.dim_venue"
def wai_ext_venueid_name(request):
	venuid = 0
	if request.method == 'POST':
		if 'venueid' in request.POST:
			venueid = request.POST.get('venueid')
			vendetcur = connection.cursor()
			vendetcur.execute("select pk_venue, venue_name from mart.dim_venue where pk_venue = %s", [venueid])
			clirow = vendetcur.fetchall()
			vendetcur.close()
			
			for massing in clirow:
				venuid = massing[0]
		
			if venuid is None:
				venuid = 0
		
		elif 'venuename' in request.POST:
			venuname = request.POST.get('venuename')
			vendetcur= connection.cursor()
			vendetcur.execute("select pk_venue, venue_name from mart.dim_venue where venue_name like %s", [venuname])
			clirow = vendetcur.fetchall()
			vendetcur.close()
			
			for massing in clirow:
				venuid = massing[0]
		
			if venuid is None:
				venuid = 0
		else:
			venuid = 0
		
	return HttpResponse(venuid)

#Function to check Venue ID/Venue Name already exist or not "mart.dim_venue" while updating the venue name
def wai_extupdvenidna(request):
	venuid = 0
	if request.method == 'POST':
		if 'venueid' in request.POST:
			venueid = request.POST.get('venueid')
			venuname = request.POST.get('venuename')
			vendetcur = connection.cursor()
			vendetcur.execute("select pk_venue, venue_name from mart.dim_venue where venue_name like %s and pk_venue <> %s", (venuname, venueid))
			vendetrow = vendetcur.fetchall()
			vendetcur.close()
			
			for vensing in vendetrow:
				venuid = vensing[0]
		
			if venuid is None:
				venuid = 0
		else:
			venuid = 0
		
	return HttpResponse(venuid)

def wai_insvendet(request):
	usid = request.session.get("userid")
	usem = request.session.get("username")
	ustyp = request.session.get("usertype")
		
	strsysdt = datetime.datetime.now()
	strsysdt = str(strsysdt)[:19]
		
	cliid = request.GET.get("cid")
		
	if request.method == 'POST':
		#txtcrtvenuid, txtcrtvenuname, txtcrtvenudesc, txtcrtvenuaddr, txtcrtvenucity, txtcrtvenucount, txtcrtvenucur, txtcrtvenureptz, txtcrtvenuorg, txtcrtvenuuid
		strVenId = request.POST.get('txtcrtvenuid')
		strVenNa = request.POST.get('txtcrtvenuname')
		strVenDesc = request.POST.get('txtcrtvenudesc')
		strVenAdr =  request.POST.get('txtcrtvenuaddr')
		strVenCit =  request.POST.get('txtcrtvenucity')			
		strVenCout =  request.POST.get('txtcrtvenucount')
		strVenCur =  request.POST.get('txtcrtvenucur')
		strVenReTz =  request.POST.get('txtcrtvenureptz')
		strVenOrg =  request.POST.get('txtcrtvenuorg')
		strVenUID =  request.POST.get('txtcrtvenuuid')	

		insvencur = connection.cursor()
		insvencur.execute("insert into mart.dim_venue (venue_name, description, address, city, country, venue_currency, report_timezone, organization_name, venue_uuid, dw_updated_by, dw_update_date, pk_venue, pk_client) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (strVenNa, strVenDesc, strVenAdr, strVenCit, strVenCout, strVenCur, strVenReTz, strVenOrg, strVenUID, usid, strsysdt, strVenId, cliid))
		connection.commit()
		insvencur.close()
			
	strRedirect = "/wai_clivendet/?cid=" + cliid
	return HttpResponseRedirect(strRedirect)
#Manage Client/Venue Ends

#Manage Admin User Starts
def wai_mngadmuser(request):
	if 'userid' not in request.session:
		return HttpResponseRedirect('/wai_login/')
	else:
		usem = request.session.get("username")
		usid = request.session.get("userid")
		ustyp = request.session.get("usertype")

		strsysdt = datetime.datetime.now()
		strsysdt = str(strsysdt)[:19]
		if request.method == 'POST':
			arrobjusid = request.POST.getlist("hidusrid")
			arrobjusname = request.POST.getlist("txtusrname")
			arrobjusemail = request.POST.getlist("txtusremail")
			arrobjusacti = request.POST.getlist("ddlusract")
			arrobjustype = request.POST.getlist("ddlusrtype")
			
			i = 0
			while i < len(arrobjusid):
				hidusid = arrobjusid[i]
				txtusname = arrobjusname[i]
				txtusemail = arrobjusemail[i]
				txtusact = arrobjusacti[i]
				txtustype = arrobjustype[i]
				
				cursor = connection.cursor()
				cursor.execute("update wisdom_meta_data.wisdom_users set admin_username = %s, admin_emailid = %s, admin_active = %s, admin_usertype = %s, admin_updatedby = %s, admin_updatedon = %s where admin_userid = %s", (txtusname, txtusemail, txtusact, txtustype, usid, strsysdt, hidusid))
				connection.commit()
       				cursor.close()
				i = i + 1

			return HttpResponseRedirect('/wai_mngadmuser/')
		else:
			usrcur = connection.cursor()
			usrcur.execute("select admin_userid, admin_username, admin_emailid, admin_active, admin_usertype, last_loggedin, admin_createdby, admin_createon, admin_updatedby, admin_updatedon from wisdom_meta_data.wisdom_users")
		        desc = usrcur.description
       			userdet = [
       				dict(zip([col[0] for col in desc], row))
	                	for row in usrcur.fetchall()
       		        	]
	        	usrcur.close()

			pgcur = connection.cursor()
			pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
			desc = pgcur.description
       			pgdet = [
				dict(zip([col[0] for col in desc], row))
	       			for row in pgcur.fetchall()
				]
			pgcur.close()
			
			clientid = ""
			if 'clientid' in request.session:
				clientid = request.session["clientid"]

			clidetcur = connection.cursor()
			clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
			desc = clidetcur.description
			clidet = [
				dict(zip([col[0] for col in desc], row))
				for row in clidetcur.fetchall()
			]
			for row in clidet:
				if clientid == "":
					clientid = row["pk_client"]
			clidetcur.close()

			vendetcur = connection.cursor()
			vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
			desc = vendetcur.description
			vendet = [
				dict(zip([col[0] for col in desc], row))
				for row in vendetcur.fetchall()
			]
			vendetcur.close()

			return render(request, 'wai_mngadmuser.html', {'usrdet': userdet, 'userperms': "", 'hid': "5", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet })

def wai_crtuser(request):
	if 'userid' not in request.session:
		return HttpResponseRedirect('/wai_login/')
	else:
		usem = request.session.get("username")
		usid = request.session.get("userid")
		ustyp = request.session.get("usertype")

		frmsysdt = datetime.datetime.now()
		frmsysdt = str(frmsysdt)[:19]
		
		if request.method == 'POST':
			frmusname = request.POST.get("txcrtusname")
			frmusemail = request.POST.get("txtcrtusemailid")
			frmusacti = request.POST.get("ddlcrtusactive")
			frmustype = request.POST.get("ddlcrtustype")
			frmpwd = ''.join([choice('1234567890qwertyuiopasdfghjklzxcvbnm') for i in range(7)])

			usrcur = connection.cursor()
			usrcur.execute("insert into wisdom_meta_data.wisdom_users (admin_username, admin_emailid, admin_active, admin_usertype, admin_createdby, admin_createon, admin_password) values (%s, %s, %s, %s, %s, %s, %s)", (frmusname, frmusemail, frmusacti, frmustype, usid, frmsysdt, frmpwd))
			connection.commit()
			insid = usrcur.lastrowid
		        usrcur.close()

			frmfrom = 'no-reply@venuenext.com'
			subject = 'Activation request'
			html_content = 'Dear '+frmusname+'<br /><br />Welcome! to our admin portal, your account has recently added to the admin portal. Your credentials are given below: <br /><br />User Name :'+frmusemail+'<br />Password: '+frmpwd+'<br /><br />Thanks<br />Admin Team'
			msg = EmailMessage(subject, html_content, frmfrom, [frmusemail])
			msg.content_subtype = "html"  # Main content is now text/html
			msg.send()

			#send_mail('Activation request', '', 'no-reply@venuenext.com', [frmusemail], fail_silently=False)

			usrdetcur = connection.cursor()
			usrdetcur.execute("select admin_userid, admin_username, admin_emailid, admin_active, admin_usertype, last_loggedin, admin_createdby, admin_createon, admin_updatedby, admin_updatedon from wisdom_meta_data.wisdom_users order by admin_userid desc limit 1")
			userrow = usrdetcur.fetchall()
			
			lastinsid = ""
			
			for usrsing in userrow:
				lastinsid = usrsing[0]
		        usrdetcur.close()

			
			#ddlpagename, hidview, hidedit, hiddel

			arrDDLPageName = request.POST.getlist('ddlpagename')
			arrHidView = request.POST.getlist('hidview')
			arrHidEdit =  request.POST.getlist('hidedit')
			arrHidDel =  request.POST.getlist('hiddel')
			i = 0
			while i < len(arrDDLPageName):
				frmPgName = arrDDLPageName[i]
				frmPgView = arrHidView[i]
				frmPgEdit = arrHidEdit[i]
				frmPgDel = "N" # arrHidDel[i]
				
				cursor = connection.cursor()
				cursor.execute("insert into wisdom_meta_data.wisdom_user_permissions (admin_userid, page_name, page_view, page_edit, page_delete, created_by, created_on) values (%s, %s, %s, %s, %s, %s, %s)", (lastinsid, frmPgName, frmPgView, frmPgEdit, frmPgDel, usid, frmsysdt))
				connection.commit()
       				cursor.close()
				i = i + 1

			return HttpResponseRedirect('/wai_mngadmuser/')

#Function to check User Name already exist or not "wisdom_meta_data.wisdom_users"
def wai_extusridna(request):
	extusrid = 0
	if request.method == 'POST':
		if 'usid' in request.POST:
			usid = request.POST.get('usid')
			usrname = request.POST.get('usname')
			usrdetcur = connection.cursor()
			usrdetcur.execute("select admin_userid, admin_username from wisdom_meta_data.wisdom_users where admin_emailid like %s and admin_userid <> %s", (usrname, usid))
			usrrow = usrdetcur.fetchall()
			usrdetcur.close()
			
			for ussing in usrrow:
				extusrid = ussing[0]
		
			if extusrid is None:
				extusrid = 0
		
		elif 'usrname' in request.POST:
			usrname = request.POST.get('usrname')
			usrdetcur= connection.cursor()
			usrdetcur.execute("select admin_userid, admin_username from wisdom_meta_data.wisdom_users where admin_emailid like %s", [usrname])
			usrrow = usrdetcur.fetchall()
			usrdetcur.close()
			
			for ussing in usrrow:
				extusrid = ussing[0]
		
			if extusrid is None:
				extusrid = 0
		else:
			extusrid = 0
		
	return HttpResponse(extusrid)

def wai_usrpermission(request):
	if request.POST.has_key('hidusridper'):
		usrid = request.POST['hidusridper']
		cursor = connection.cursor()
		cursor.execute("select permission_id, admin_userid, page_name, page_view, page_edit, page_delete, created_by, created_on from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s", [usrid])
		desc = cursor.description
       		userperms = [
       			dict(zip([col[0] for col in desc], row))
	        	for row in cursor.fetchall()       			
		]
       		cursor.close()
		html = render_to_string('wai_usrpermiss.html', {'userperms': userperms, 'updusid': usrid })
        	return HttpResponse(html)

def wai_usrupdperms(request):
	if 'userid' not in request.session:
		return HttpResponseRedirect('/wai_login/')
	else:
		usem = request.session.get("username")
		usid = request.session.get("userid")
		ustyp = request.session.get("usertype")

		frmsysdt = datetime.datetime.now()
		frmsysdt = str(frmsysdt)[:19]
		if request.method == 'POST':
			hidusid = request.POST.get("hidupdusid")
			#ddlupdpgna, chkupdview, hidupdview, chkupdedit, hidupdedit, chkupddelet, hidupddel
			
			arrDDLPageName = request.POST.getlist('ddlupdpgna')
			arrHidView = request.POST.getlist('hidupdview')
			arrHidEdit =  request.POST.getlist('hidupdedit')
			#arrHidDel =  request.POST.getlist('hidupddel')
			arrHidPerID =  request.POST.getlist('hidupdpermid')
			i = 0
			while i < len(arrDDLPageName):
				strPgName = arrDDLPageName[i]
				strPgView = arrHidView[i]
				strPgEdit = arrHidEdit[i]
				strPgDel = "N" #arrHidDel[i]
				intPerID = arrHidPerID[i]
				
				cursor = connection.cursor()
				cursor.execute("update wisdom_meta_data.wisdom_user_permissions set page_name = %s, page_view = %s, page_edit = %s, page_delete = %s, updated_by = %s, updated_on = %s where permission_id = %s", (strPgName, strPgView, strPgEdit, strPgDel, usid, frmsysdt, intPerID))
				connection.commit()
       				cursor.close()
				i = i + 1
				
			return HttpResponseRedirect('/wai_mngadmuser/')

#Manage Admin User Ends

#Following function will show based on the client selection venue name will display
def wai_loadvenudet(request):
	if request.POST.has_key('clieid'):
		clientid = request.POST['clieid']
		venueid = ""
		vendetcur = connection.cursor()
		vendetcur.execute("select pk_venue, venue_name from mart.dim_venue where pk_client = %s", [clientid])
		desc = vendetcur.description
       		dsvendet = [
       			dict(zip([col[0] for col in desc], row))
	        	for row in vendetcur.fetchall()
		]
		for row in dsvendet:
			if venueid == "":
				venueid = row["pk_venue"]

       		vendetcur.close()
#		if 'clientid' in request.session:
#	 		del request.session["clientid"]

#		if 'venueid' in request.session:
#	 		del request.session["venueid"]
			
		request.session["clientid"] = clientid
		request.session["venueid"] = venueid

		html = render_to_string('wai_ddlvendet.html', {'dsvendet': dsvendet })
        	return HttpResponse(html)

#Following function will set the session for venue
def wai_sessionvenuid(request):
	if request.POST.has_key('venueid'):
		venueid = request.POST['venueid']
		
#		if 'venueid' in request.session:
#	 		del request.session["venueid"]
			
		request.session["venueid"] = venueid
        	return HttpResponse('SUCCESS')

#Black Out Calendar Starts
def wai_mngblacal(request):
	usid = request.session.get("userid")
	usem = request.session.get("username")
	ustyp = request.session.get("usertype")
	
	pgcur = connection.cursor()
	pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
	desc = pgcur.description
	pgdet = [
		dict(zip([col[0] for col in desc], row))
		for row in pgcur.fetchall()
		]
	pgcur.close()
	
	blacaldet = ""
	if request.method == "POST":
		blacaldetcur = connection.cursor()
		blacaldetcur.execute("SELECT wbc.pk_client, wbc.pk_venue, wbc.blackout_key, wbc.blackout_value, wbc.dw_create_date, wbc.dw_update_date, wbc.dw_created_by, wbc.dw_updated_by, dc.client_name, dv.venue_name FROM wisdom_meta_data.wisdom_blackout_calendar wbc, mart.dim_client dc, mart.dim_venue dv where wbc.pk_client = dc.pk_client and wbc.pk_venue = dv.pk_venue")
		desc = blacaldetcur.description
		blacaldet = [
			dict(zip([col[0] for col in desc], row))
			for row in blacaldetcur.fetchall()
		]
		blacaldetcur.close()	
	else:
		blacaldetcur = connection.cursor()
		blacaldetcur.execute("SELECT wbc.pk_client, wbc.pk_venue, wbc.blackout_key, wbc.blackout_value, wbc.dw_create_date, wbc.dw_update_date, wbc.dw_created_by, wbc.dw_updated_by, dc.client_name, dv.venue_name FROM wisdom_meta_data.wisdom_blackout_calendar wbc, mart.dim_client dc, mart.dim_venue dv where wbc.pk_client = dc.pk_client and wbc.pk_venue = dv.pk_venue")
		desc = blacaldetcur.description
		blacaldet = [
			dict(zip([col[0] for col in desc], row))
			for row in blacaldetcur.fetchall()
		]
		blacaldetcur.close()
	
	clientid = ""
	if 'clientid' in request.session:
		clientid = request.session["clientid"]

	clidetcur = connection.cursor()
	clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
	desc = clidetcur.description
    	clidet = [
    		dict(zip([col[0] for col in desc], row))
		for row in clidetcur.fetchall()
	]
	for row in clidet:
        	if clientid == "":
        		clientid = row["pk_client"]

	clidetcur.close()
	vendetcur = connection.cursor()
	vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
	desc = vendetcur.description
	vendet = [
		dict(zip([col[0] for col in desc], row))
		for row in vendetcur.fetchall()
	]
	vendetcur.close()
	
	return render(request, 'wai_mngblacal.html', {'blacaldet': blacaldet,'hid': "51", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet  })

#This function insert a new record in "wisdom_meta_data.wisdom_blackout_calendar" table
def wai_mngcreblacal(request):
	if request.method == 'POST':
		usid = request.session.get("userid")
		usem = request.session.get("username")
		ustyp = request.session.get("usertype")

		frmsysdt = datetime.datetime.now()
	        frmsysdt = str(frmsysdt)[:19]
		frmclient = request.POST.get("ddlblacalclie") 
		frmvenue = request.POST.get("ddlblacalvenu")
	        frmblakey = request.POST.get("txtblacalkey")
        	frmblaval = request.POST.get("txtblacalval")

	        cursor = connection.cursor()

        	cursor.execute("INSERT INTO wisdom_meta_data.wisdom_blackout_calendar(pk_client, pk_venue, blackout_key, blackout_value, dw_create_date, dw_created_by) VALUES (%s, %s, %s, %s, %s, 'MANUAL')", (frmclient, frmvenue, frmblakey, frmblaval, frmsysdt))
	        connection.commit()
        	cursor.close()
		return HttpResponse('SUCCESS')
	else:
	    	return HttpResponse('FAILED')
#Black Out Calendar Ends


#Levis Event Calendar Starts
def wai_mnglevevtcal(request):
	usid = request.session.get("userid")
	usem = request.session.get("username")
	ustyp = request.session.get("usertype")
	
	pgcur = connection.cursor()
	pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
	desc = pgcur.description
	pgdet = [
		dict(zip([col[0] for col in desc], row))
		for row in pgcur.fetchall()
		]
	pgcur.close()
	
	clientid = ""
	if 'clientid' in request.session:
		clientid = request.session["clientid"]

	clidetcur = connection.cursor()
	clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
	desc = clidetcur.description
    	clidet = [
    		dict(zip([col[0] for col in desc], row))
		for row in clidetcur.fetchall()
	]
	for row in clidet:
        	if clientid == "":
        		clientid = row["pk_client"]
	clidetcur.close()
	
	vendetcur = connection.cursor()
	vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
	desc = vendetcur.description
	vendet = [
		dict(zip([col[0] for col in desc], row))
		for row in vendetcur.fetchall()
	]
	vendetcur.close()
	
	return render(request, 'wai_mnglevevtcal.html', {'hid': "52", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet })
#Levis Event Calendar Ends


#Livenation Event Calendar Starts
def wai_mnglivevt(request):
	usid = request.session.get("userid")
	usem = request.session.get("username")
	ustyp = request.session.get("usertype")
	
	pgcur = connection.cursor()
	pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
	desc = pgcur.description
	pgdet = [
		dict(zip([col[0] for col in desc], row))
		for row in pgcur.fetchall()
		]
	pgcur.close()

	livnatdet = "";
	if request.method == "POST":
		livnatdetcur = connection.cursor()
		livnatdetcur.execute("select wes.pk_client, wes.pk_venue, wes.entry_timezone, wes.dw_create_date, wes.dw_created_by, wes.dw_update_date, wes.dw_updaated_by, wes.start_time, wes.end_time, dc.client_name, dv.venue_name from wisdom_meta_data.wisdom_event_scheduling wes, mart.dim_client dc, mart.dim_venue dv where wes.pk_client = dc.pk_client and wes.pk_venue = dv.pk_venue and wes.pk_client = 3")
		desc = livnatdetcur.description
		livnatdet = [
			dict(zip([col[0] for col in desc], row))
			for row in livnatdetcur.fetchall()
		]
		livnatdetcur.close()	
	else:
		livnatdetcur = connection.cursor()
		livnatdetcur.execute("select wes.pk_client, wes.pk_venue, wes.entry_timezone, wes.dw_create_date, wes.dw_created_by, wes.dw_update_date, wes.dw_updaated_by, wes.start_time, wes.end_time, dc.client_name, dv.venue_name from wisdom_meta_data.wisdom_event_scheduling wes, mart.dim_client dc, mart.dim_venue dv where wes.pk_client = dc.pk_client and wes.pk_venue = dv.pk_venue and wes.pk_client = 3")
		desc = livnatdetcur.description
		livnatdet = [
			dict(zip([col[0] for col in desc], row))
			for row in livnatdetcur.fetchall()
		]
		livnatdetcur.close()

	clientid = ""
	if 'clientid' in request.session:
		clientid = request.session["clientid"]

	clidetcur = connection.cursor()
	clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
	desc = clidetcur.description
    	clidet = [
    		dict(zip([col[0] for col in desc], row))
		for row in clidetcur.fetchall()
	]
	for row in clidet:
        	if clientid == "":
        		clientid = row["pk_client"]
	clidetcur.close()
	
	vendetcur = connection.cursor()
	vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
	desc = vendetcur.description
	vendet = [
		dict(zip([col[0] for col in desc], row))
		for row in vendetcur.fetchall()
	]
	vendetcur.close()
	
	return render(request, 'wai_mnglivevtcal.html', {'livnatdet': livnatdet, 'hid': "53", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet })	
#Livenation Event Calendar Ends

#Configuration Management Starts
def wai_mngcon(request):
	usid = request.session.get("userid")
	usem = request.session.get("username")
	ustyp = request.session.get("usertype")
	
	pgcur = connection.cursor()
	pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
	desc = pgcur.description
	pgdet = [
		dict(zip([col[0] for col in desc], row))
		for row in pgcur.fetchall()
		]
	pgcur.close()

	clientid = ""
	if 'clientid' in request.session:
		clientid = request.session["clientid"]

	clidetcur = connection.cursor()
	clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
	desc = clidetcur.description
    	clidet = [
    		dict(zip([col[0] for col in desc], row))
		for row in clidetcur.fetchall()
	]
	for row in clidet:
        	if clientid == "":
        		clientid = row["pk_client"]
	clidetcur.close()
	
	vendetcur = connection.cursor()
	vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
	desc = vendetcur.description
	vendet = [
		dict(zip([col[0] for col in desc], row))
		for row in vendetcur.fetchall()
	]
	vendetcur.close()
	
	return render(request, 'wai_mngcon.html', {'hid': "31", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet })
#Configuration Management Ends

#Splunk Activity Starts
def wai_mngsplact(request):
	usid = request.session.get("userid")
	usem = request.session.get("username")
	ustyp = request.session.get("usertype")
	
	pgcur = connection.cursor()
	pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
	desc = pgcur.description
	pgdet = [
		dict(zip([col[0] for col in desc], row))
		for row in pgcur.fetchall()
		]
	pgcur.close()
	
	clientid = ""
	if 'clientid' in request.session:
		clientid = request.session["clientid"]

	clidetcur = connection.cursor()
	clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
	desc = clidetcur.description
    	clidet = [
    		dict(zip([col[0] for col in desc], row))
		for row in clidetcur.fetchall()
	]
	for row in clidet:
        	if clientid == "":
        		clientid = row["pk_client"]
	clidetcur.close()
	
	vendetcur = connection.cursor()
	vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
	desc = vendetcur.description
	vendet = [
		dict(zip([col[0] for col in desc], row))
		for row in vendetcur.fetchall()
	]
	vendetcur.close()
	
	return render(request, 'wai_mngsplroles.html', {'hid': "41", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet })

#Splunk Create Roles starts
def wai_mngsplcrtrol(request):
	usid = request.session.get("userid")
	usem = request.session.get("username")
	ustyp = request.session.get("usertype")
	
	pgcur = connection.cursor()
	pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
	desc = pgcur.description
	pgdet = [
		dict(zip([col[0] for col in desc], row))
		for row in pgcur.fetchall()
		]
	pgcur.close()
	
	clientid = ""
	if 'clientid' in request.session:
		clientid = request.session["clientid"]

	clidetcur = connection.cursor()
	clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
	desc = clidetcur.description
    	clidet = [
    		dict(zip([col[0] for col in desc], row))
		for row in clidetcur.fetchall()
	]
	for row in clidet:
        	if clientid == "":
        		clientid = row["pk_client"]
	clidetcur.close()
	
	vendetcur = connection.cursor()
	vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
	desc = vendetcur.description
	vendet = [
		dict(zip([col[0] for col in desc], row))
		for row in vendetcur.fetchall()
	]
	vendetcur.close()
	
	return render(request, 'wai_mngsplroles.html', {'hid': "42", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet })


def submit_role(request):
	usid = request.session.get("userid")
	usem = request.session.get("username")
	ustyp = request.session.get("usertype")
	
	pgcur = connection.cursor()
	pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
	desc = pgcur.description
	pgdet = [
		dict(zip([col[0] for col in desc], row))
		for row in pgcur.fetchall()
		]
	pgcur.close()
	
	clientid = ""
	if 'clientid' in request.session:
		clientid = request.session["clientid"]

	clidetcur = connection.cursor()
	clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
	desc = clidetcur.description
    	clidet = [
    		dict(zip([col[0] for col in desc], row))
		for row in clidetcur.fetchall()
	]
	for row in clidet:
        	if clientid == "":
        		clientid = row["pk_client"]
	clidetcur.close()
	
	vendetcur = connection.cursor()
	vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
	desc = vendetcur.description
	vendet = [
		dict(zip([col[0] for col in desc], row))
		for row in vendetcur.fetchall()
	]
	vendetcur.close()

	try:
    		if request.GET['client_name'] == '' or request.GET['venue_name'] == '':
		        raise Exception("Please provide the client and venue name")
    
    		venue_name=str(request.GET['venue_name'])
		client_name =str(request.GET['client_name'])
		role_name=request.GET['client_name']+"_"+request.GET['venue_name']
		imported_roles=[]
		imported_roles=str(request.GET['imported_roles']).split(',')
		search_filter='"'+str(request.GET['search_fltr'])+'"'
    
		if str(request.GET['search_fltr']) == '':
			search_filter = '"'+'venue_name='+venue_name+' OR report_parameters.venue_name='+venue_name+' OR Client='+client_name +'"'

		hostnames=[]
		hostnames.append('wisdom-dev-ssplunk-0.venuenext.net')
		hostnames.append('wisdom-dev-ssplunk-1.venuenext.net')

		search_indexes=str(request.GET['srchIndexesAllowed']).split(',')
		default_app=str(request.GET['defaultApp'])
    		#return HttpResponse(role_name + " " + imported_roles + " " + searrchFilter + " " + str(hostnames[0]))
		for host in hostnames:
        		result, cmd_execute=splunk_api.createSplunkRole(userName,userPassword,host,managementPort,name=role_name,imported_roles=imported_roles,srchFilter=search_filter,srchIndexesAllowed=search_indexes,defaultApp=default_app)
		
		#return HttpResponse(cmd_execute +" " +result)    
		return render(request, 'wai_splrolessucc.html', {'hid': "42", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet, 'cmd_execute': cmd_execute, 'result': "Splunk roles are created successfully" })
	except Exception, e:
		return render(request, 'wai_splrolessucc.html', {'hid': "42", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet, 'result': e })

#Splunk Create Roles Ends
    

#Splunk Create User starts
def wai_mngsplcrtusr(request):
    #return render(request, 'create_users.html')
	usid = request.session.get("userid")
	usem = request.session.get("username")
	ustyp = request.session.get("usertype")
	
	pgcur = connection.cursor()
	pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
	desc = pgcur.description
	pgdet = [
		dict(zip([col[0] for col in desc], row))
		for row in pgcur.fetchall()
		]
	pgcur.close()
	
	clientid = ""
	if 'clientid' in request.session:
		clientid = request.session["clientid"]

	clidetcur = connection.cursor()
	clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
	desc = clidetcur.description
    	clidet = [
    		dict(zip([col[0] for col in desc], row))
		for row in clidetcur.fetchall()
	]
	for row in clidet:
        	if clientid == "":
        		clientid = row["pk_client"]
	clidetcur.close()
	
	vendetcur = connection.cursor()
	vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
	desc = vendetcur.description
	vendet = [
		dict(zip([col[0] for col in desc], row))
		for row in vendetcur.fetchall()
	]
	vendetcur.close()
	
	return render(request, 'wai_mngspluser.html', {'hid': "41", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet })


def submit_user(request):
	usid = request.session.get("userid")
	usem = request.session.get("username")
	ustyp = request.session.get("usertype")
	
	pgcur = connection.cursor()
	pgcur.execute("select page_name, page_view, page_edit, page_delete from wisdom_meta_data.wisdom_user_permissions where admin_userid = %s and page_view = 'Y' order by permission_id asc", [usid])
	desc = pgcur.description
	pgdet = [
		dict(zip([col[0] for col in desc], row))
		for row in pgcur.fetchall()
		]
	pgcur.close()
	
	clientid = ""
	if 'clientid' in request.session:
		clientid = request.session["clientid"]

	clidetcur = connection.cursor()
	clidetcur.execute("select pk_client, client_name from mart.dim_client order by client_name asc;")
	desc = clidetcur.description
    	clidet = [
    		dict(zip([col[0] for col in desc], row))
		for row in clidetcur.fetchall()
	]
	for row in clidet:
        	if clientid == "":
        		clientid = row["pk_client"]
	clidetcur.close()
	
	vendetcur = connection.cursor()
	vendetcur.execute("SELECT pk_venue, venue_name FROM mart.dim_venue where pk_client = %s;",[clientid])
	desc = vendetcur.description
	vendet = [
		dict(zip([col[0] for col in desc], row))
		for row in vendetcur.fetchall()
	]
	vendetcur.close()
	
	try:
    		if request.GET['user_name'] == '' or request.GET['password'] == '' or request.GET['roles'] == '' or request.GET['timezone'] == ''  :
        		raise Exception("Please provide the username, password, roles and timezone")

		user_name=str(request.GET['user_name'])
		password=str(request.GET['password'])
		roles=[]
		roles=str(request.GET['roles']).split(',')
		timezone=str(request.GET['timezone'])
		hostnames=[]
		hostnames.append('wisdom-dev-ssplunk-0.venuenext.net')
		hostnames.append('wisdom-dev-ssplunk-1.venuenext.net')

		for host in hostnames:
        		result, cmd_execute=splunk_api.createSplunkUser(userName,userPassword,host,managementPort,name=user_name,password=password,roles=roles,tz=timezone)
	
	       	#return HttpResponse(cmd_execute +" " +result)    
		return render(request, 'wai_splusrsucc.html', {'hid': "41", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet, 'cmd_execute': cmd_execute, 'result': "Splunk user created successfully" })
	except Exception, e:
		return render(request, 'wai_splusrsucc.html', {'hid': "41", 'usna': usem, 'ustyp': ustyp, 'pgdet': pgdet, 'clidet': clidet, 'vendet': vendet, 'result': "Could not create user: " + str(e) })

#Splunk Create User ends


#Splunk Activity Ends

# Common Header Check
def wai_header(request):
	frmto = 'Karthik@venuenext.com, rajesh@venuenext.com'
	frmfrom = 'no-reply@venuenext.com'
	#send_mail('Mails from django server', 'testing the mail for django server is responding.', frmfrom , [frmto], fail_silently=False)

	randompass = ''.join([choice('1234567890qwertyuiopasdfghjklzxcvbnm') for i in range(7)])

	html_content = 'Testing the mail for <Strong>django server is responding,</strong> if we using html tags inside the body. <br /><br />pwd is : '+randompass
	subject = 'Html format mail with random pass gen'
	msg = EmailMessage(subject, html_content, frmfrom, [frmto])
	msg.content_subtype = "html"  # Main content is now text/html
	msg.send()

	return render(request, 'name.html', {'valdet': "Mail was sent successfully." })

#Checking the ajax call working
def main(request):
	return render(request, 'ajaxhtml.html')
#   	return render_to_response('ajaxhtml.html', context_instance=RequestContext(request))

def ajax(request):
   if request.POST.has_key('txtname'):
        name = request.POST['txtname']
	pwd = request.POST['txtpwd']
	name = name, " ", pwd
        return HttpResponse(name)
   else:
        return render_to_response('ajaxhtml.html', context_instance=RequestContext(request))
#ajax call ends

#The following function will show a particular fields from the select query
def viewvalmasdet(request):
        valfuldet = ""
        cursor = connection.cursor()
        cursor.execute("SELECT id, code, description, associated_entity, category, threshold_value, status, project_id, priority, active_flag, validation_query FROM validation.wisdom_data_validation_master order by id asc")
        desc = cursor.description
        valfuldet = [
                dict(zip([col[0] for col in desc], row))
                for row in cursor.fetchall()
                ]
        cursor.close()
        return render(request, 'validate.html', {'valdet': valfuldet })

#The following function will show the form fields that is newly generated
def get_name(request):
        usname = ""
        if request.method == 'POST':
		form = NameForm(request.POST)
                if form.is_valid():
                        usname = form.cleaned_data['username']
                        txtcode = form.cleaned_data['code']
                        getnamconstr = "host='wisdom-dev-pgres.crqcj0aw0zmu.us-west-1.rds.amazonaws.com' dbname='wisdom_qa' user='wisdomadmin' password='W!sd0madmin'"
                        getnamconn = psycopg2.connect(getnamconstr)
                        cursor = getnamconn.cursor()

#                       cursor.execute("insert into user_details (username) values ('usname');")
#                       transaction.commit()
                        getnamconn.close()
                        return render(request, 'story/home.html', {'name': usname, 'addr': txtcode })
#               return HttpResponseRedirect('/home/')
        else:
                form = NameForm()

	fmt = "%Y-%m-%d %H:%M:%S %Z%z"
	
	cursysdt = datetime.datetime.now()
	#cursysdt = str(cursysdt)[:10]
	#cursysdt = datetime.datetime.strptime(cursysdt, '%Y-%m-%d').strftime('%m/%d/%Y')

	#Asia/Kolkata to change the timezone to IST
	# Current time in IST
	now_ist = cursysdt

	# Convert to US/Pacific time zone
	now_pacific = now_ist.astimezone(timezone('US/Pacific'))

	# Convert to Europe/Berlin time zone
	now_berlin = now_pacific.astimezone(timezone('Europe/Berlin'))

        return render(request, 'name.html', {'form': form, 'now_ist': now_ist, 'now_pacific': now_pacific, 'now_berlin': now_berlin })
