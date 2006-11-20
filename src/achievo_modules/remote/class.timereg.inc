<?php
include_once (moduleDir("timestats")."class.hours.inc");

//XML stuff da http://www.xml.com/pub/a/2003/03/19/dive-into-xml.html
if (stristr($_SERVER[HTTP_ACCEPT], "application/xhtml+xml")) 
    header("Content-Type: application/xhtml+xml");
else
    header("Content-Type: text/html");
    
function is_valid_date($date)
{
	return (ereg("([0-9]{4}).([0-9]{1,2}).([0-9]{1,2})", $date));
}

function make_xml($msg, $results, $bodykey="")
{
	$res  = '<?xml version="1.0" encoding="ISO-8859-1"?>'."\n";
	$res .= '<response msg="'.htmlspecialchars($msg).'" len="'.count($results).'">'."\n";
	foreach ($results as $r)
	{
		$res .= "<record";
		foreach ($r as $key=>$value)
		{
			if ($key != $bodykey)
				$res .= ' '.htmlspecialchars($key).'="'.htmlspecialchars($value).'"';
		}
		if (array_key_exists($bodykey, $r))
		{
			$res .= ">\n";
			$res .= htmlspecialchars($r[$bodykey])."\n";
			$res .= "</record>\n";
		}
		else
			$res .= " />\n";

	}
	$res .= '</response>';
	return $res;
}

class timereg extends atkNode
{
	function timereg()
	{
		$this->atkNode("timereg");
	}

	function action_save()
	{
		atkdebug("timereg Action save");
		$hoursnode = &atkGetNode("timereg.hours");
		$hoursnode->m_postvars = $this->m_postvars; // Share postvars.
		$record = $hoursnode->updateRecord();

		$hoursnode->preAdd($record);
		$hoursnode->validate($record, "add");

		$error = count($record['atkerror']) > 0;
		foreach (array_keys($record) as $key)
			$error = $error || (is_array($record[$key]) && count($record[$key]['atkerror']) > 0);

		if ($error)
        {
            echo make_xml("Err", $error);
		}
		else
		{
			$hoursnode->addDb($record, true, "add");
			echo make_xml("OK", "add");

		}
		exit;
	}
}
?>
