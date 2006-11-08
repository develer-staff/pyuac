<?php
include_once (moduleDir("timestats")."class.hours.inc");

class timereg extends hours
{
	function timereg()
	{
		$this->atkNode("timereg");
		hours::hours();
	}

	function action_save()
	{
		atkdebug("Action save");
		$record = $this->updateRecord();

		$this->preAdd($record);

		$this->validate($record, "add");

		$error = count($record['atkerror']) > 0;
		foreach (array_keys($record) as $key)
			$error = $error || (is_array($record[$key]) && count($record[$key]['atkerror']) > 0);

		if ($error)
		{
			echo "Err: $error";
		}
		else
		{
			$this->addDb($record, true, "add");
			echo "OK";
		}

		exit;
	}
}
?>
