valstatusst = 0
valstatused = 1

valproist = 1
valproied = 2

function trimAllSpace(str) 
{ 
    var str1 = ''; 
    var i = 0; 
    while(i != str.length) 
    { 
        if(str.charAt(i) != ' ') 
            str1 = str1 + str.charAt(i); i ++; 
    } 
    return str1; 
}

function trimString(str) 
{ 
     var str1 = ''; 
     var i = 0; 
     while ( i != str.length) 
     { 
         if(str.charAt(i) != ' ') str1 = str1 + str.charAt(i); i++; 
     }
     var retval = IsNumeric(str1); 
     if(retval == false) 
         return -100; 
     else 
         return str1; 
}

var specialKeys = new Array();
specialKeys.push(8); //Backspace
function IsNumeric(e) {
	var keyCode = e.which ? e.which : e.keyCode
	var ret = ((keyCode >= 48 && keyCode <= 57) || specialKeys.indexOf(keyCode) != -1);
	return ret;
}

function IsNumericwithDot(e) {
	var keyCode = e.which ? e.which : e.keyCode
	var ret = ((keyCode >= 48 && keyCode <= 57) || (keyCode == 46) || specialKeys.indexOf(keyCode) != -1);
	return ret;
}

function emailChecker (emailStr)
{	
	var emailPat=/^(.+)@(.+)$/
	var specialChars="\\(\\)<>@,;:\\\\\\\"\\.\\[\\]"
	var validChars="\[^\\s" + specialChars + "\]"
	var quotedUser="(\"[^\"]*\")"
	var ipDomainPat=/^\[(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\]$/
	var atom=validChars + '+'
	var word="(" + atom + "|" + quotedUser + ")"
	var userPat=new RegExp("^" + word + "(\\." + word + ")*$")
	var domainPat=new RegExp("^" + atom + "(\\." + atom +")*$")
	var matchArray=emailStr.match(emailPat)
	if (matchArray==null) 
	{
		alert('Please enter valid e-mail.');
		return false;
	}
	var user=matchArray[1]
	var domain=matchArray[2]
	if (user.match(userPat)==null)
	{
		alert('Please enter the valid e-mail.');
		return false;
	}

	var IPArray=domain.match(ipDomainPat)
	if (IPArray!=null) 
	{
		for (var i=1;i<=4;i++) 
		{
			if (IPArray[i]>255) 
			{
				alert('Please enter the valid e-mail.');
				return false;
			}
		}
		return true;
	}
	var domainArray=domain.match(domainPat)
	if (domainArray==null) 
	{
		alert('Please enter the valid e-mail.');
		return false;
	}
	var atomPat=new RegExp(atom,"g")
	var domArr=domain.match(atomPat)
	var len=domArr.length
	if (domArr[domArr.length-1].length<2 || domArr[domArr.length-1].length>3) 
	{
		alert('Email must end in a three-letter domain, or two letter country.');
		return false
	}
	if (len<2)
	{
		alert('Please enter valid e-mail.');
		return false;
	}
	return true;
}